import React, { useState, useCallback, useEffect } from 'react'; // Added useEffect
import { Circle, Save, Loader2 as SpinnerIcon, AlertTriangle } from 'lucide-react'; // Added AlertTriangle
// useToast is now used within the mutation hook directly for success/error.

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton'; // For loading state
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import AutobidSettingsForm, { AutobidSettingsFormValues, autobidSettingsSchema } from '@/components/settings/AutobidSettingsForm';
import { 
  useAllAutobidSettings, 
  useUpdateAllAutobidSettings 
} from '@/hooks/useAutobidSettingsQueries';
import type { ProfileWithSettings, ProfileForSettings } from '@/services/autobidSettingsService'; // Import types
import { useToast } from '@/hooks/useToast';


export default function AutobidSettingsPage() {
  const { data: fetchedSettings, isLoading, isError, error } = useAllAutobidSettings();
  const updateSettingsMutation = useUpdateAllAutobidSettings();
  const { showToastError } = useToast(); // For local validation errors

  // Local state to hold editable settings, initialized from fetched data
  const [editableSettings, setEditableSettings] = useState<ProfileWithSettings[]>([]);
  
  // State to control which accordion items are open by default
  const [openAccordionItems, setOpenAccordionItems] = useState<string[]>([]);

  useEffect(() => {
    if (fetchedSettings) {
      setEditableSettings(fetchedSettings);
      // Optionally, open the first accordion item by default if not already set
      if (fetchedSettings.length > 0 && openAccordionItems.length === 0) {
        setOpenAccordionItems([fetchedSettings[0].profile.id]);
      }
    }
  }, [fetchedSettings]); // Removed openAccordionItems from dependency array to avoid re-triggering

  const handleSettingsChange = useCallback((profileId: string, newSettings: AutobidSettingsFormValues) => {
    setEditableSettings(prev =>
      prev.map(pws =>
        pws.profile.id === profileId ? { ...pws, settings: newSettings } : pws
      )
    );
  }, []);

  const handleSaveAllSettings = async () => {
    console.log("Attempting to save all settings...");

    // Client-side validation for all forms
    let allValid = true;
    for (const pws of editableSettings) {
      try {
        autobidSettingsSchema.parse(pws.settings); // Validate each setting object
      } catch (validationError) {
        allValid = false;
        // Highlight the accordion item with the error or scroll to it
        // For now, just log and show a general error
        console.error(`Validation failed for profile ${pws.profile.name}:`, validationError);
        // Open the accordion item if it's not already open to show the error
        if (!openAccordionItems.includes(pws.profile.id)) {
          setOpenAccordionItems(prev => [...prev, pws.profile.id]);
        }
      }
    }

    if (!allValid) {
      showToastError("Some settings are invalid. Please check the forms and correct them.");
      return;
    }

    try {
      await updateSettingsMutation.mutateAsync(editableSettings);
      // Success toast is handled by the mutation hook's onSuccess
    } catch (e) {
      // Error toast is handled by the mutation hook's onError
      console.error("Failed to save all settings:", e);
    }
  };
  
  const onAccordionValueChange = (value: string[]) => {
    setOpenAccordionItems(value);
  };

  if (isLoading) {
    return (
      <div className="p-4 md:p-6 space-y-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Skeleton className="h-10 w-64 mb-2" /> {/* Title Skeleton */}
            <Skeleton className="h-4 w-96" /> {/* Description Skeleton */}
          </div>
          <Skeleton className="h-12 w-48" /> {/* Button Skeleton */}
        </div>
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="border rounded-lg bg-card p-4">
            <Skeleton className="h-8 w-1/2 mb-4" /> {/* Accordion Trigger Skeleton */}
            <Skeleton className="h-40 w-full" /> {/* Form Content Skeleton */}
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 md:p-6 text-center max-w-4xl mx-auto">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
        <h2 className="mt-4 text-xl font-semibold text-red-600">Error Loading Autobid Settings</h2>
        <p className="mt-2 text-muted-foreground">{error?.message || "An unexpected error occurred."}</p>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Autobid Settings</h1>
          <p className="text-muted-foreground">
            Configure automatic bidding preferences for each of your profiles.
          </p>
        </div>
        <Button onClick={handleSaveAllSettings} disabled={updateSettingsMutation.isPending} size="lg">
          {updateSettingsMutation.isPending ? (
            <SpinnerIcon className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <Save className="mr-2 h-5 w-5" />
          )}
          Save All Settings
        </Button>
      </div>

      {editableSettings.length === 0 && !isLoading && (
        <p className="text-center text-muted-foreground py-8">
          No profiles found or settings available. Please ensure profiles exist.
        </p>
      )}

      <Accordion 
        type="multiple"
        value={openAccordionItems}
        onValueChange={onAccordionValueChange} 
        className="w-full space-y-4"
      >
        {editableSettings.map(({ profile, settings }) => (
          <AccordionItem key={profile.id} value={profile.id} className="border rounded-lg bg-card">
            <AccordionTrigger className="px-6 py-4 hover:no-underline">
              <div className="flex items-center space-x-3">
                <Circle 
                  className={`h-3 w-3 ${settings.isEnabled ? 'fill-green-500 text-green-500' : 'fill-gray-300 text-gray-300'}`} 
                />
                <span className="text-lg font-medium">{profile.name}</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-6 pt-0 pb-6 border-t">
              <div className="pt-4">
                <AutobidSettingsForm
                  profileId={profile.id}
                  initialData={settings}
                  onSettingsChange={handleSettingsChange}
                />
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}

// Temporary Card component for skeleton loading, assuming it's not globally available here
// In a real setup, this would be imported from ui/card or a shared components directory
const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={`rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}
    {...props}
  />
);
