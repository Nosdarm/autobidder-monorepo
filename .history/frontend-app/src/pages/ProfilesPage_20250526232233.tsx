import React, { useState, useEffect, useCallback } from 'react';
import { profileService, Profile, ProfileCreate, ProfileUpdate } from '@/services/profileService';
import { AuthProvider, useAuth } from './components/contexts/AuthContext';

// Conceptual imports for shadcn/ui - replace with actual implementations later
// import { Button } from '@/components/ui/button';
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
// import { useToast } from '@/components/ui/use-toast';

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<any>(null);
  
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  
  // const { toast } = useToast(); // Conceptual

  const fetchProfiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await profileService.getAllProfiles();
      setProfiles(data);
    } catch (err) {
      setError(err);
      // toast({ variant: "destructive", title: "Error fetching profiles", description: (err as Error).message });
      alert(`Error fetching profiles: ${(err as Error).message} (Conceptual Toast)`);
    } finally {
      setIsLoading(false);
    }
  }, []); // Removed toast from dependencies

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleCreate = () => {
    setEditingProfile(null);
    setIsModalOpen(true);
  };

  const handleEdit = (profile: Profile) => {
    setEditingProfile(profile);
    setIsModalOpen(true);
  };

  const handleDelete = async (profileId: string) => {
    // Conceptual: Use a proper confirmation dialog
    if (window.confirm('Are you sure you want to delete this profile?')) {
      try {
        await profileService.deleteProfile(profileId);
        // toast({ title: "Profile Deleted", description: "Profile successfully deleted." });
        alert('Profile successfully deleted. (Conceptual Toast)');
        fetchProfiles(); // Refresh list
      } catch (err) {
        setError(err); // Show error at page level or use toast
        // toast({ variant: "destructive", title: "Error deleting profile", description: (err as Error).message });
        alert(`Error deleting profile: ${(err as Error).message} (Conceptual Toast)`);
      }
    }
  };

  const handleSaveProfile = async (profileData: ProfileCreate | ProfileUpdate) => {
    try {
      if (editingProfile) {
        await profileService.updateProfile(editingProfile.id, profileData as ProfileUpdate);
        // toast({ title: "Profile Updated", description: "Profile successfully updated." });
        alert('Profile successfully updated. (Conceptual Toast)');
      } else {
        await profileService.createProfile(profileData as ProfileCreate);
        // toast({ title: "Profile Created", description: "Profile successfully created." });
        alert('Profile successfully created. (Conceptual Toast)');
      }
      fetchProfiles(); // Refresh list
      setIsModalOpen(false);
      setEditingProfile(null);
    } catch (err) {
      // Error handling is tricky in modals. Could pass setError to modal or use toast.
      console.error("Save profile error:", err);
      // toast({ variant: "destructive", title: "Save failed", description: (err as Error).message });
      alert(`Save failed: ${(err as Error).message} (Conceptual Toast)`);
      // Optionally, keep modal open if save fails: throw err;
    }
  };

  if (isLoading) return <p>Loading profiles...</p>;
  if (error) return <p style={{ color: 'red' }}>Error loading profiles: {error.message}</p>;

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Profiles Management</h1>
        {/* Conceptual Button */}
        <button 
          onClick={handleCreate}
          style={{ padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          Create Profile
        </button>
      </div>

      {/* Conceptual Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Name</th>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Type</th>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Autobid Enabled</th>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Skills</th>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Experience</th>
            <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {profiles.map((profile) => (
            <tr key={profile.id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{profile.name}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{profile.profile_type}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{profile.autobid_enabled ? 'Yes' : 'No'}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{profile.skills?.join(', ') || 'N/A'}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{profile.experience_level || 'N/A'}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                {/* Conceptual Buttons */}
                <button 
                  onClick={() => handleEdit(profile)}
                  style={{ marginRight: '5px', padding: '6px 12px', backgroundColor: '#ffc107', border: 'none', borderRadius: '4px' }}
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleDelete(profile.id)}
                  style={{ padding: '6px 12px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {profiles.length === 0 && !isLoading && (
            <tr>
              <td colSpan={6} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>
                No profiles found.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {isModalOpen && (
        <ProfileFormModal
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setEditingProfile(null);
          }}
          profileToEdit={editingProfile}
          onSave={handleSaveProfile}
        />
      )}
    </div>
  );
}
