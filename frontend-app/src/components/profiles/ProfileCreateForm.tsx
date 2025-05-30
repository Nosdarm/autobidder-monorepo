import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next'; // Import useTranslation

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { DialogFooter } from '@/components/ui/dialog';

// Function to create schema with translated messages
const createProfileFormSchema = (t: (key: string) => string) => z.object({
  id: z.string().optional(),
  name: z.string()
    .nonempty({ message: t('profileForm.validation.nameRequired') })
    .min(3, { message: t('profileForm.validation.nameMinLength', { min: 3 }) }),
  type: z.enum(["personal", "agency"], {
    required_error: t('profileForm.validation.typeRequired'),
  }),
  autobidEnabled: z.boolean().default(false),
  skills: z.array(z.string()).optional(),
  experience_level: z.string().optional(),
});

export type ProfileFormValues = z.infer<ReturnType<typeof createProfileFormSchema>>;

// Internationalization keys:
// profileForm.skillsLabel: "Skills"
// profileForm.skillsPlaceholder: "e.g., React, Node.js, Python"
// profileForm.skillsDescription: "Enter skills separated by commas."
// profileForm.experienceLevelLabel: "Experience Level"
// profileForm.experienceLevelPlaceholder: "Select experience level"
// profileForm.experienceEntryLevel: "Entry-level"
// profileForm.experienceIntermediate: "Intermediate"
// profileForm.experienceExpert: "Expert"
// profileForm.agencySpecificFieldLabel: "Agency Specific Field (e.g., Company Name)"
// profileForm.agencySpecificFieldPlaceholder: "Enter company name"
// profileForm.agencySpecificFieldDescription: "This field is specific to agency profiles."


interface ProfileCreateFormProps {
  userAccountType: 'individual' | 'agency'; // Added userAccountType prop
  onSave: (data: ProfileFormValues) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  initialData?: ProfileFormValues | null;
}

export default function ProfileCreateForm({ userAccountType, onSave, onCancel, isSaving, initialData }: ProfileCreateFormProps) {
  const { t } = useTranslation(); // Initialize useTranslation
  const profileFormSchema = createProfileFormSchema(t); // Create schema with t function

  const defaultProfileType = userAccountType === 'individual' ? 'personal' : (initialData?.type || undefined);

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: initialData || {
      id: undefined,
      name: '',
      type: defaultProfileType, // Set default type based on userAccountType
      autobidEnabled: false,
      skills: [],
      experience_level: undefined,
    },
  });

  const { handleSubmit, control, reset, watch } = form;

  // Watch the value of the 'type' field to conditionally render other fields
  const profileTypeBeingCreated = watch('type');

  useEffect(() => {
    if (initialData) {
      reset(initialData);
    } else {
      reset({
        id: undefined,
        name: '',
        type: defaultProfileType,
        autobidEnabled: false,
        skills: [],
        experience_level: undefined,
      });
    }
  }, [initialData, reset, defaultProfileType]);

  // Effect to set profile type if userAccountType is individual and it's a new form
  useEffect(() => {
    if (userAccountType === 'individual' && !initialData?.id) {
      form.setValue('type', 'personal');
    }
  }, [userAccountType, initialData, form]);

  const submitButtonText = initialData?.id 
    ? t("profileForm.saveButtonUpdate") 
    : t("profileForm.saveButtonCreate");

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit(onSave)} className="space-y-6">
        <FormField
          control={control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('profileForm.nameLabel')}</FormLabel>
              <FormControl>
                <Input placeholder={t('profileForm.namePlaceholder')} {...field} />
              </FormControl>
              <FormDescription>
                {t('profileForm.nameDescription')}
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        
        {/* Conditional Fields based on profileTypeBeingCreated */}
        {(profileTypeBeingCreated === 'personal' || !profileTypeBeingCreated) && ( // Show if personal or type not yet selected
          <>
            <FormField
              control={control}
              name="skills"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profileForm.skillsLabel', 'Skills')}</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder={t('profileForm.skillsPlaceholder', 'e.g., React, Node.js, Python')} 
                      {...field} 
                      value={Array.isArray(field.value) ? field.value.join(', ') : ''}
                      onChange={(e) => field.onChange(e.target.value.split(',').map(skill => skill.trim()).filter(skill => skill))}
                    />
                  </FormControl>
                  <FormDescription>
                    {t('profileForm.skillsDescription', 'Enter skills separated by commas.')}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={control}
              name="experience_level"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profileForm.experienceLevelLabel', 'Experience Level')}</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t('profileForm.experienceLevelPlaceholder', 'Select experience level')} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="entry">{t('profileForm.experienceEntryLevel', 'Entry-level')}</SelectItem>
                      <SelectItem value="intermediate">{t('profileForm.experienceIntermediate', 'Intermediate')}</SelectItem>
                      <SelectItem value="expert">{t('profileForm.experienceExpert', 'Expert')}</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {/* Add description if needed */}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        )}

        {/* Profile Type Field - visibility based on userAccountType */}
        {userAccountType === 'agency' && (
          <FormField
            control={control}
            name="type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('profileForm.typeLabel')}</FormLabel>
                <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder={t('profileForm.typePlaceholder')} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="personal">{t('profileForm.typePersonal')}</SelectItem>
                    <SelectItem value="agency">{t('profileForm.typeAgency')}</SelectItem>
                  </SelectContent>
                </Select>
                <FormDescription>
                  {t('profileForm.typeDescription')}
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        )}
        {/* For individual users, 'type' is not shown but will be set to 'personal' by default or effect */}

        {/* Agency Specific Field - only if profileTypeBeingCreated is 'agency' */}
        {profileTypeBeingCreated === 'agency' && (
           <FormField
            // This is a placeholder field, not part of the actual form schema/submission yet
            control={control} // Using control to make it part of the form structure for RHF
            name="agencySpecificField" // A dummy name, not in ProfileFormValues
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('profileForm.agencySpecificFieldLabel', 'Agency Specific Field (e.g., Company Name)')}</FormLabel>
                <FormControl>
                  <Input placeholder={t('profileForm.agencySpecificFieldPlaceholder', 'Enter company name')} {...field} />
                </FormControl>
                <FormDescription>
                  {t('profileForm.agencySpecificFieldDescription', 'This field is specific to agency profiles.')}
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        <FormField
          control={control}
          name="autobidEnabled"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">{t('profileForm.autobidLabel')}</FormLabel>
                <FormDescription>
                  {t('profileForm.autobidDescription')}
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
            {t('profileForm.cancelButton')}
          </Button>
          <Button type="submit" disabled={isSaving}>
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            {submitButtonText}
          </Button>
        </DialogFooter>
      </form>
    </Form>
  );
}
