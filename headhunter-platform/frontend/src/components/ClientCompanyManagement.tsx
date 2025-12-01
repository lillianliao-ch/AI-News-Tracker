'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from './AuthProvider'

interface CompanyClient {
  id: string
  name: string
  industry?: string
  size?: string
  contactName: string
  contactPhone: string
  contactEmail?: string
  location?: string
  tags?: string[]
  status: 'active' | 'suspended' | 'terminated'
  partnerCompany?: {
    id: string
    name: string
  }
  maintainer: {
    id: string
    username: string
    email: string
  }
  _count: {
    jobs: number
  }
  createdAt: string
}

interface CreateClientData {
  name: string
  industry?: string
  size?: string
  contactName: string
  contactPhone: string
  contactEmail?: string
  location?: string
  tags?: string[]
}

export default function ClientCompanyManagement() {
  const { user } = useAuth()
  const [clients, setClients] = useState<CompanyClient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filters, setFilters] = useState({
    industry: '',
    location: '',
    search: '',
    status: ''
  })

  const [newClient, setNewClient] = useState<CreateClientData>({
    name: '',
    industry: '',
    size: '',
    contactName: '',
    contactPhone: '',
    contactEmail: '',
    location: '',
    tags: []
  })

  const fetchClients = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10',
        ...Object.fromEntries(Object.entries(filters).filter(([_, value]) => value))
      })
      
      const response = await api.getCompanyClients({
        page,
        limit: 10,
        ...Object.fromEntries(Object.entries(filters).filter(([_, value]) => value))
      })
      setClients(response.companyClients || [])
      setTotalPages(response.pagination?.pages || 1)
    } catch (err) {
      setError('Failed to fetch client companies')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const createClient = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      console.log('Creating client with data:', newClient)
      await api.post('/company-clients', newClient)
      setShowCreateForm(false)
      setNewClient({
        name: '',
        industry: '',
        size: '',
        contactName: '',
        contactPhone: '',
        contactEmail: '',
        location: '',
        tags: []
      })
      fetchClients()
    } catch (err: any) {
      console.error('Create client error:', err)
      const errorMessage = err.response?.data?.message || err.message || 'Failed to create client company'
      setError(errorMessage)
    }
  }

  const deleteClient = async (clientId: string) => {
    if (confirm('Are you sure you want to delete this client company?')) {
      try {
        await api.delete(`/company-clients/${clientId}`)
        fetchClients()
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to delete client company')
      }
    }
  }

  const updateClientStatus = async (clientId: string, newStatus: 'active' | 'suspended' | 'terminated') => {
    const action = newStatus === 'terminated' ? 'terminate cooperation' : 
                   newStatus === 'suspended' ? 'suspend cooperation' : 'reactivate cooperation'
    
    if (confirm(`Are you sure you want to ${action} with this client?`)) {
      try {
        await api.patch(`/company-clients/${clientId}/status`, {
          status: newStatus
        })
        fetchClients()
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to update client status')
      }
    }
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'suspended':
        return 'bg-yellow-100 text-yellow-800'
      case 'terminated':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active'
      case 'suspended':
        return 'Suspended'
      case 'terminated':
        return 'Terminated'
      default:
        return status
    }
  }

  useEffect(() => {
    fetchClients()
  }, [page, filters])

  if (loading) return <div className="p-6">Loading client companies...</div>

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Client Company Management</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add New Client
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search clients..."
            value={filters.search}
            onChange={(e) => setFilters({...filters, search: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          />
          <input
            type="text"
            placeholder="Industry"
            value={filters.industry}
            onChange={(e) => setFilters({...filters, industry: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          />
          <input
            type="text"
            placeholder="Location"
            value={filters.location}
            onChange={(e) => setFilters({...filters, location: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="terminated">Terminated</option>
          </select>
        </div>
      </div>

      {/* Client List */}
      <div className="space-y-4">
        {clients.map((client) => (
          <div key={client.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center space-x-3">
                  <h3 className="text-lg font-semibold text-gray-900">{client.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(client.status)}`}>
                    {getStatusText(client.status)}
                  </span>
                </div>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                  {client.industry && <span>{client.industry}</span>}
                  {client.location && <span>{client.location}</span>}
                  {client.size && <span>{client.size}</span>}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  {client._count.jobs} jobs
                </span>
                
                {/* Status Change Buttons */}
                {user?.role === 'company_admin' && (
                  <>
                    {client.status === 'active' && (
                      <>
                        <button
                          onClick={() => updateClientStatus(client.id, 'suspended')}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                        >
                          Suspend
                        </button>
                        <button
                          onClick={() => updateClientStatus(client.id, 'terminated')}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Terminate
                        </button>
                      </>
                    )}
                    {client.status === 'suspended' && (
                      <>
                        <button
                          onClick={() => updateClientStatus(client.id, 'active')}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                        >
                          Reactivate
                        </button>
                        <button
                          onClick={() => updateClientStatus(client.id, 'terminated')}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Terminate
                        </button>
                      </>
                    )}
                    {client.status === 'terminated' && (
                      <button
                        onClick={() => updateClientStatus(client.id, 'active')}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        Reactivate
                      </button>
                    )}
                  </>
                )}
                
                {user?.role === 'company_admin' && (
                  <button
                    onClick={() => deleteClient(client.id)}
                    className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Contact: {client.contactName}</p>
                <p className="text-gray-600">Phone: {client.contactPhone}</p>
                {client.contactEmail && (
                  <p className="text-gray-600">Email: {client.contactEmail}</p>
                )}
              </div>
              <div>
                {client.partnerCompany && (
                  <p className="text-gray-600">Partner: {client.partnerCompany.name}</p>
                )}
                <p className="text-gray-600">
                  Maintained by: {client.maintainer.username}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex justify-center mt-6">
        <div className="flex space-x-2">
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      {/* Create Client Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Add New Client Company</h2>
              <form onSubmit={createClient} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newClient.name}
                    onChange={(e) => setNewClient({...newClient, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Industry
                    </label>
                    <input
                      type="text"
                      value={newClient.industry}
                      onChange={(e) => setNewClient({...newClient, industry: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Size
                    </label>
                    <select
                      value={newClient.size}
                      onChange={(e) => setNewClient({...newClient, size: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    >
                      <option value="">Select size</option>
                      <option value="1-10">1-10 employees</option>
                      <option value="11-50">11-50 employees</option>
                      <option value="51-200">51-200 employees</option>
                      <option value="201-500">201-500 employees</option>
                      <option value="500+">500+ employees</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newClient.contactName}
                    onChange={(e) => setNewClient({...newClient, contactName: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Phone *
                    </label>
                    <input
                      type="tel"
                      required
                      value={newClient.contactPhone}
                      onChange={(e) => setNewClient({...newClient, contactPhone: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={newClient.contactEmail}
                      onChange={(e) => setNewClient({...newClient, contactEmail: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    value={newClient.location}
                    onChange={(e) => setNewClient({...newClient, location: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  />
                </div>

                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Create Client
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}