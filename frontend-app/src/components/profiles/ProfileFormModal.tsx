import React, { useState, useEffect } from 'react';
import { Profile, ProfileCreate, ProfileUpdate } from '@/services/profileService';

// Conceptual imports for shadcn/ui - replace with actual implementations later
// import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription, DialogClose } from '@/components/ui/dialog';
// import { Button } from '@/components/ui/button';
// import { Input } from '@/components/ui/input';
// import { Label } from '@/components/ui/label';
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// import { Checkbox } from '@/components/ui/checkbox';
// import { useToast } from '@/components/ui/use-toast';

interface ProfileFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  profileToEdit?: Profile | null;
  onSave: (profileData: ProfileCreate | ProfileUpdate) => Promise<void>;
}

export default function ProfileFormModal({
  isOpen,
  onClose,
  profileToEdit,
  onSave,
}: ProfileFormModalProps) {
  const [name, setName] = useState('');
  const [profileType, setProfileType] = useState<'personal' | 'agency'>('personal');
  const [autobidEnabled, setAutobidEnabled] = useState(false);
  const [skills, setSkills] = useState(''); // Storing as comma-separated string for simple input
  const [experienceLevel, setExperienceLevel] = useState('');
  
  const [isSaving, setIsSaving] = useState(false);
  // const { toast } = useToast(); // Conceptual

  useEffect(() => {
    if (profileToEdit) {
      setName(profileToEdit.name);
      setProfileType(profileToEdit.profile_type);
      setAutobidEnabled(profileToEdit.autobid_enabled || false);
      setSkills(profileToEdit.skills?.join(', ') || '');
      setExperienceLevel(profileToEdit.experience_level || '');
    } else {
      // Reset form for new profile
      setName('');
      setProfileType('personal');
      setAutobidEnabled(false);
      setSkills('');
      setExperienceLevel('');
    }
  }, [profileToEdit, isOpen]); // Re-initialize form when profileToEdit changes or modal opens

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    
    const skillsArray = skills.split(',').map(s => s.trim()).filter(s => s);

    const profileData: ProfileCreate | ProfileUpdate = {
      name,
      profile_type: profileType,
      autobid_enabled: autobidEnabled,
      skills: skillsArray.length > 0 ? skillsArray : null, // Send null if empty, or [] based on backend
      experience_level: experienceLevel || null, // Send null if empty
    };

    try {
      await onSave(profileData);
      // onClose(); // Success: close modal (handled by ProfilesPage onSave success)
    } catch (error) {
      // Error is handled in ProfilesPage's handleSaveProfile
      // toast({ variant: "destructive", title: "Error", description: (error as Error).message || "Failed to save profile." });
      console.error("Error in modal save:", error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  // Conceptual Modal Structure using basic HTML elements
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 50
    }}>
      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', width: '400px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        {/* Conceptual DialogHeader */}
        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          {profileToEdit ? 'Edit Profile' : 'Create New Profile'}
        </h2>
        
        {/* Conceptual DialogContent */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="profile-name" style={{ display: 'block', marginBottom: '0.5rem' }}>Name (Conceptual Label)</label>
            <input
              id="profile-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="profile-type" style={{ display: 'block', marginBottom: '0.5rem' }}>Profile Type (Conceptual Label)</label>
            <select
              id="profile-type"
              value={profileType}
              onChange={(e) => setProfileType(e.target.value as 'personal' | 'agency')}
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="personal">Personal</option>
              <option value="agency">Agency</option>
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="profile-skills" style={{ display: 'block', marginBottom: '0.5rem' }}>Skills (comma-separated) (Conceptual Label)</label>
            <input
              id="profile-skills"
              type="text"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g., python, react, fastapi"
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="profile-experience" style={{ display: 'block', marginBottom: '0.5rem' }}>Experience Level (Conceptual Label)</label>
            <input
              id="profile-experience"
              type="text"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              placeholder="e.g., entry, intermediate, expert"
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center' }}>
            <input
              id="autobid-enabled"
              type="checkbox"
              checked={autobidEnabled}
              onChange={(e) => setAutobidEnabled(e.target.checked)}
              style={{ marginRight: '0.5rem' }}
            />
            <label htmlFor="autobid-enabled">Autobid Enabled (Conceptual Checkbox)</label>
          </div>

          {/* Conceptual DialogFooter */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
            {/* Conceptual DialogClose Button */}
            <button 
              type="button" 
              onClick={onClose}
              disabled={isSaving}
              style={{ padding: '8px 16px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={isSaving}
              style={{ padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
            >
              {isSaving ? 'Saving...' : 'Save Profile'} (Conceptual Button)
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
