FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build application for production
RUN npm run build

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]