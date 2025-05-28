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
});

export type ProfileFormValues = z.infer<ReturnType<typeof createProfileFormSchema>>;

interface ProfileCreateFormProps {
  onSave: (data: ProfileFormValues) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  initialData?: ProfileFormValues | null;
}

export default function ProfileCreateForm({ onSave, onCancel, isSaving, initialData }: ProfileCreateFormProps) {
  const { t } = useTranslation(); // Initialize useTranslation
  const profileFormSchema = createProfileFormSchema(t); // Create schema with t function

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: initialData || {
      id: undefined,
      name: '',
      type: undefined, 
      autobidEnabled: false,
    },
  });

  const { handleSubmit, control, reset } = form;

  useEffect(() => {
    if (initialData) {
      reset(initialData);
    } else {
      reset({
        id: undefined,
        name: '',
        type: undefined,
        autobidEnabled: false,
      });
    }
  }, [initialData, reset]);

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
