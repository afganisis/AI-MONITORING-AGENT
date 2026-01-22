import React, { useState, useEffect } from 'react';
import { Search, Users, Building2, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';

interface Driver {
  driver_id: string;
  driver_name: string;
}

interface Company {
  company_id: string;
  company_name: string;
  drivers: Driver[];
}

const Companies: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);
  const [selectedDriverIds, setSelectedDriverIds] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  // Fetch companies on mount
  useEffect(() => {
    fetchCompanies();
    fetchSelectedDrivers();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/companies');

      if (!response.ok) {
        throw new Error('Failed to fetch companies');
      }

      const data = await response.json();
      setCompanies(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching companies:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSelectedDrivers = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/drivers/selected');

      if (response.ok) {
        const driverIds = await response.json();
        setSelectedDriverIds(new Set(driverIds));
      }
    } catch (err) {
      console.error('Error fetching selected drivers:', err);
    }
  };

  const handleCompanyClick = (companyId: string) => {
    setSelectedCompanyId(selectedCompanyId === companyId ? null : companyId);
  };

  const handleDriverToggle = (driverId: string) => {
    const newSelected = new Set(selectedDriverIds);

    if (newSelected.has(driverId)) {
      newSelected.delete(driverId);
    } else {
      newSelected.add(driverId);
    }

    setSelectedDriverIds(newSelected);
  };

  const handleSelectAllDrivers = (company: Company) => {
    const newSelected = new Set(selectedDriverIds);
    const companyDriverIds = company.drivers.map(d => d.driver_id);
    const allSelected = companyDriverIds.every(id => newSelected.has(id));

    if (allSelected) {
      // Deselect all from this company
      companyDriverIds.forEach(id => newSelected.delete(id));
    } else {
      // Select all from this company
      companyDriverIds.forEach(id => newSelected.add(id));
    }

    setSelectedDriverIds(newSelected);
  };

  const handleSaveSelection = async () => {
    try {
      setSaving(true);

      const response = await fetch('http://localhost:8000/api/drivers/select', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          driver_ids: Array.from(selectedDriverIds)
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save selection');
      }

      alert(`Successfully selected ${selectedDriverIds.size} drivers for AI Agent monitoring!`);
    } catch (err) {
      alert('Error saving selection: ' + (err instanceof Error ? err.message : 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const filteredCompanies = companies.filter(company =>
    company.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedCompany = companies.find(c => c.company_id === selectedCompanyId);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="p-6 bg-red-900/20 border-red-500">
          <p className="text-red-400">Error: {error}</p>
          <Button onClick={fetchCompanies} className="mt-4">
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Companies & Drivers
          </h1>
          <p className="text-gray-400">
            Select drivers for AI Agent monitoring
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Badge variant="info" className="text-lg px-4 py-2">
            {selectedDriverIds.size} Selected
          </Badge>

          <Button
            onClick={handleSaveSelection}
            disabled={selectedDriverIds.size === 0 || saving}
            className="bg-cyan-600 hover:bg-cyan-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Save Selection
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-cyber-800 border border-cyber-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Companies List */}
        <Card className="p-6">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center">
            <Building2 className="w-5 h-5 mr-2 text-cyan-400" />
            Companies ({filteredCompanies.length})
          </h2>

          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {filteredCompanies.map((company) => {
              const selectedCount = company.drivers.filter(d =>
                selectedDriverIds.has(d.driver_id)
              ).length;
              const isActive = company.company_id === selectedCompanyId;

              return (
                <div
                  key={company.company_id}
                  onClick={() => handleCompanyClick(company.company_id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    isActive
                      ? 'bg-cyan-900/30 border-cyan-500'
                      : 'bg-cyber-700 border-cyber-600 hover:border-cyber-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-white">
                        {company.company_name}
                      </h3>
                      <p className="text-sm text-gray-400 mt-1">
                        {company.drivers.length} drivers
                      </p>
                    </div>

                    {selectedCount > 0 && (
                      <Badge variant="success">
                        {selectedCount} selected
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Drivers List */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-cyan-400" />
              Drivers
            </h2>

            {selectedCompany && (
              <Button
                onClick={() => handleSelectAllDrivers(selectedCompany)}
                variant="secondary"
                size="sm"
              >
                {selectedCompany.drivers.every(d => selectedDriverIds.has(d.driver_id))
                  ? 'Deselect All'
                  : 'Select All'}
              </Button>
            )}
          </div>

          {!selectedCompany ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <p>Select a company to view drivers</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {selectedCompany.drivers.map((driver) => {
                const isSelected = selectedDriverIds.has(driver.driver_id);

                return (
                  <div
                    key={driver.driver_id}
                    onClick={() => handleDriverToggle(driver.driver_id)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-green-900/30 border-green-500'
                        : 'bg-cyber-700 border-cyber-600 hover:border-cyber-500'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {isSelected ? (
                          <CheckCircle2 className="w-5 h-5 text-green-400" />
                        ) : (
                          <XCircle className="w-5 h-5 text-gray-500" />
                        )}

                        <div>
                          <h3 className="font-semibold text-white">
                            {driver.driver_name}
                          </h3>
                          <p className="text-xs text-gray-400 mt-1">
                            {driver.driver_id.substring(0, 8)}...
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* Info Box */}
      {selectedDriverIds.size > 0 && (
        <Card className="p-4 bg-cyan-900/20 border-cyan-500">
          <p className="text-cyan-300">
            <strong>{selectedDriverIds.size} drivers selected.</strong> AI Agent will monitor and fix errors only for these drivers when started.
          </p>
        </Card>
      )}
    </div>
  );
};

export default Companies;
