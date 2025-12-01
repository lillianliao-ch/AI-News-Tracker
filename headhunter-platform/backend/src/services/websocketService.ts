import { Server as SocketServer, Socket } from 'socket.io';
import { Server as HttpServer } from 'http';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { UserRole } from '@/types';

interface AuthenticatedSocket extends Socket {
  userId?: string;
  userRole?: UserRole;
  companyId?: string;
}

export class WebSocketService {
  private io: SocketServer;
  private prisma: PrismaClient;
  private connectedUsers: Map<string, string[]> = new Map(); // userId -> socketIds

  constructor(server: HttpServer, prisma: PrismaClient) {
    this.prisma = prisma;
    this.io = new SocketServer(server, {
      cors: {
        origin: true,
        credentials: true,
      },
    });

    this.setupAuthentication();
    this.setupEventHandlers();
  }

  private setupAuthentication() {
    this.io.use(async (socket: any, next) => {
      try {
        const token = socket.handshake.auth.token || socket.handshake.headers.authorization?.replace('Bearer ', '');
        
        if (!token) {
          return next(new Error('Authentication token required'));
        }

        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production') as any;
        
        // Get user details from database
        const user = await this.prisma.user.findUnique({
          where: { id: decoded.userId },
          select: {
            id: true,
            role: true,
            status: true,
            companyId: true,
          },
        });

        if (!user || user.status !== 'active') {
          return next(new Error('User not found or inactive'));
        }

        socket.userId = user.id;
        socket.userRole = user.role;
        socket.companyId = user.companyId;
        
        next();
      } catch (error) {
        next(new Error('Invalid authentication token'));
      }
    });
  }

  private setupEventHandlers() {
    this.io.on('connection', (socket: any) => {
      console.log(`User ${socket.userId} connected via WebSocket`);

      // Track connected user
      this.addUserConnection(socket.userId, socket.id);

      // Join user-specific room
      socket.join(`user:${socket.userId}`);
      
      // Join company room if user belongs to a company
      if (socket.companyId) {
        socket.join(`company:${socket.companyId}`);
      }

      // Join role-based room
      socket.join(`role:${socket.userRole}`);

      // Handle disconnection
      socket.on('disconnect', () => {
        console.log(`User ${socket.userId} disconnected from WebSocket`);
        this.removeUserConnection(socket.userId, socket.id);
      });

      // Handle ping/pong for connection health
      socket.on('ping', () => {
        socket.emit('pong');
      });

      // Handle typing indicators for chat
      socket.on('typing:start', (data: { roomId: string }) => {
        socket.to(data.roomId).emit('typing:start', {
          userId: socket.userId,
          roomId: data.roomId,
        });
      });

      socket.on('typing:stop', (data: { roomId: string }) => {
        socket.to(data.roomId).emit('typing:stop', {
          userId: socket.userId,
          roomId: data.roomId,
        });
      });

      // Handle notification acknowledgment
      socket.on('notification:read', async (data: { notificationId: string }) => {
        try {
          await this.prisma.notification.updateMany({
            where: {
              id: data.notificationId,
              recipientId: socket.userId,
            },
            data: { isRead: true },
          });
          
          socket.emit('notification:read:success', { notificationId: data.notificationId });
        } catch (error) {
          socket.emit('notification:read:error', { 
            notificationId: data.notificationId,
            error: 'Failed to mark notification as read',
          });
        }
      });

      // Send initial status
      socket.emit('connected', {
        userId: socket.userId,
        userRole: socket.userRole,
        companyId: socket.companyId,
        timestamp: new Date().toISOString(),
      });
    });
  }

  private addUserConnection(userId: string, socketId: string) {
    const connections = this.connectedUsers.get(userId) || [];
    connections.push(socketId);
    this.connectedUsers.set(userId, connections);
  }

  private removeUserConnection(userId: string, socketId: string) {
    const connections = this.connectedUsers.get(userId) || [];
    const updatedConnections = connections.filter(id => id !== socketId);
    
    if (updatedConnections.length === 0) {
      this.connectedUsers.delete(userId);
    } else {
      this.connectedUsers.set(userId, updatedConnections);
    }
  }

  // Public methods for sending notifications
  public sendNotificationToUser(userId: string, notification: any) {
    this.io.to(`user:${userId}`).emit('notification', notification);
  }

  public sendNotificationToCompany(companyId: string, notification: any) {
    this.io.to(`company:${companyId}`).emit('notification', notification);
  }

  public sendNotificationToRole(role: UserRole, notification: any) {
    this.io.to(`role:${role}`).emit('notification', notification);
  }

  public sendBroadcastNotification(notification: any) {
    this.io.emit('notification', notification);
  }

  // Real-time updates for collaboration
  public notifyJobShared(recipientIds: string[], jobData: any) {
    recipientIds.forEach(userId => {
      this.io.to(`user:${userId}`).emit('job:shared', jobData);
    });
  }

  public notifySubmissionStatusChanged(userId: string, submissionData: any) {
    this.io.to(`user:${userId}`).emit('submission:status-changed', submissionData);
  }

  public notifyMaintainerChangeRequest(recipientIds: string[], requestData: any) {
    recipientIds.forEach(userId => {
      this.io.to(`user:${userId}`).emit('maintainer-change:requested', requestData);
    });
  }

  public notifyMaintainerChangeReviewed(recipientIds: string[], reviewData: any) {
    recipientIds.forEach(userId => {
      this.io.to(`user:${userId}`).emit('maintainer-change:reviewed', reviewData);
    });
  }

  // System announcements
  public sendSystemAnnouncement(announcement: any, targetRole?: UserRole, targetCompanyId?: string) {
    if (targetRole) {
      this.io.to(`role:${targetRole}`).emit('system:announcement', announcement);
    } else if (targetCompanyId) {
      this.io.to(`company:${targetCompanyId}`).emit('system:announcement', announcement);
    } else {
      this.io.emit('system:announcement', announcement);
    }
  }

  // Get connection status
  public isUserConnected(userId: string): boolean {
    return this.connectedUsers.has(userId);
  }

  public getConnectedUsers(): string[] {
    return Array.from(this.connectedUsers.keys());
  }

  public getConnectionCount(): number {
    return this.connectedUsers.size;
  }

  // Health check for WebSocket service
  public getHealthStatus() {
    return {
      connected: true,
      connectedUsers: this.getConnectionCount(),
      totalSockets: this.io.engine.clientsCount,
      uptime: process.uptime(),
    };
  }
}

let websocketService: WebSocketService;

export const initializeWebSocketService = (server: HttpServer, prisma: PrismaClient) => {
  websocketService = new WebSocketService(server, prisma);
  return websocketService;
};

export const getWebSocketService = (): WebSocketService => {
  if (!websocketService) {
    throw new Error('WebSocket service not initialized');
  }
  return websocketService;
};