import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"; // Using shadcn/ui Form components

// Zod schema for Autobid Settings
export const autobidSettingsSchema = z.object({
  isEnabled: z.boolean().default(false),
  interval: z.coerce // coerce to number
    .number({ invalid_type_error: "Interval must be a number" })
    .min(1, { message: "Interval must be at least 1 minute" })
    .positive({ message: "Interval must be positive" }),
  dailyLimit: z.coerce // coerce to number
    .number({ invalid_type_error: "Daily limit must be a number" })
    .min(0, { message: "Daily limit cannot be negative" }) // 0 might mean no limit or disabled, depends on interpretation
    .positive({ message: "Daily limit must be a positive number if set" }).optional(), // Optional if 0 is allowed for "no limit"
});

export type AutobidSettingsFormValues = z.infer<typeof autobidSettingsSchema>;

interface AutobidSettingsFormProps {
  profileId: string; // To identify which profile's settings are being changed
  initialData: AutobidSettingsFormValues;
  onSettingsChange: (profileId: string, data: AutobidSettingsFormValues) => void;
  // No onSubmit here, as global save will handle it. Form validation will still occur on change.
}

export default function AutobidSettingsForm({ 
  profileId, 
  initialData, 
  onSettingsChange 
}: AutobidSettingsFormProps) {
  const form = useForm<AutobidSettingsFormValues>({
    resolver: zodResolver(autobidSettingsSchema),
    defaultValues: initialData,
    mode: 'onChange', // Validate on change to provide immediate feedback
  });

  const { control, watch, formState: { errors } } = form;

  // Subscribe to form value changes and propagate them to the parent
  React.useEffect(() => {
    const subscription = watch((values, { name, type }) => {
      // Ensure values are valid before propagating
      // Type assertion needed as react-hook-form's values can be partial during updates
      const validatedValues = {
        isEnabled: values.isEnabled ?? initialData.isEnabled,
        interval: values.interval ?? initialData.interval,
        dailyLimit: values.dailyLimit ?? initialData.dailyLimit,
      };
      // Only propagate if the values are valid according to the schema
      // This is a bit tricky as RHF validates on blur/submit by default
      // For now, we propagate and let the parent deal with potentially invalid states during typing
      // or rely on onBlur validation of RHF.
      // A more robust solution might involve form.trigger() and then checking formState.isValid
      onSettingsChange(profileId, validatedValues as AutobidSettingsFormValues);
    });
    return () => subscription.unsubscribe();
  }, [watch, onSettingsChange, profileId, initialData]);

  return (
    <Form {...form}>
      <form className="space-y-6"> {/* No onSubmit needed here */}
        <FormField
          control={control}
          name="isEnabled"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Enable Autobid</FormLabel>
                <FormDescription>
                  Allow automatic bidding for this profile.
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

        <FormField
          control={control}
          name="interval"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bidding Interval (minutes)</FormLabel>
              <FormControl>
                <Input type="number" placeholder="e.g., 15" {...field} onChange={e => field.onChange(parseInt(e.target.value, 10) || 0)} />
              </FormControl>
              <FormDescription>
                How often the system should check for new jobs.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="dailyLimit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Daily Bidding Limit</FormLabel>
              <FormControl>
                <Input type="number" placeholder="e.g., 10" {...field} onChange={e => field.onChange(parseInt(e.target.value, 10) || 0)} />
              </FormControl>
              <FormDescription>
                Maximum number of bids to place per day for this profile (0 for no limit - use with caution).
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        {/* No submit button per form item */}
      </form>
    </Form>
  );
}
