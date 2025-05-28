import React, { useEffect } from 'react'; // Added useEffect
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// Label is not directly used, FormLabel from ui/form is used.
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { DialogFooter } from '@/components/ui/dialog';

// Define Zod schema for profile creation/editing
const profileFormSchema = z.object({
  id: z.string().optional(), // ID will be present when editing
  name: z.string().nonempty({ message: "Profile name is required" }).min(3, { message: "Name must be at least 3 characters" }),
  type: z.enum(["personal", "agency"], {
    required_error: "Profile type is required.",
  }),
  autobidEnabled: z.boolean().default(false),
});

export type ProfileFormValues = z.infer<typeof profileFormSchema>;

interface ProfileCreateFormProps {
  onSave: (data: ProfileFormValues) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  initialData?: ProfileFormValues | null; // Optional prop for editing
}

export default function ProfileCreateForm({ onSave, onCancel, isSaving, initialData }: ProfileCreateFormProps) {
  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: initialData || { // Pre-fill if initialData exists
      id: undefined,
      name: '',
      type: undefined,
      autobidEnabled: false,
    },
  });

  const { handleSubmit, control, reset } = form; // Added reset

  // Effect to reset form when initialData changes (for editing)
  useEffect(() => {
    if (initialData) {
      reset(initialData);
    } else {
      // Reset to default empty values if creating a new profile after editing
      reset({
        id: undefined,
        name: '',
        type: undefined,
        autobidEnabled: false,
      });
    }
  }, [initialData, reset]);

  const submitButtonText = initialData?.id ? "Save Changes" : "Save Profile";

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit(onSave)} className="space-y-6">
        {/* ID field can be hidden if not needed in the form UI itself */}
        {/* <FormField control={control} name="id" render={({ field }) => <Input type="hidden" {...field} />} /> */}
        
        <FormField
          control={control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Profile Name</FormLabel>
              <FormControl>
                <Input placeholder="e.g., My Upwork Profile" {...field} />
              </FormControl>
              <FormDescription>
                A descriptive name for this profile.
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
              <FormLabel>Profile Type</FormLabel>
              <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a profile type" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="personal">Personal</SelectItem>
                  <SelectItem value="agency">Agency</SelectItem>
                </SelectContent>
              </Select>
              <FormDescription>
                Choose "personal" for individual accounts, "agency" for teams.
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
                <FormLabel className="text-base">Autobid Enabled</FormLabel>
                <FormDescription>
                  Allow automatic bidding for jobs matching this profile.
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
            Cancel
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
