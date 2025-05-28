import React, { useEffect } from 'react'; // Added useEffect
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// Label is not directly used, FormLabel from ui/form is used.
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { DrawerFooter } from '@/components/ui/drawer';

interface ProfileLike {
  id: string;
  name: string;
}

const MAX_PROMPT_LENGTH = 2000;

const promptFormSchema = z.object({
  id: z.string().optional(), // ID will be present when editing
  name: z.string().nonempty({ message: "Prompt name is required" }).min(3, { message: "Name must be at least 3 characters" }),
  promptText: z.string()
    .nonempty({ message: "Prompt text is required" })
    .max(MAX_PROMPT_LENGTH, { message: `Prompt text must be ${MAX_PROMPT_LENGTH} characters or less` }),
  profileId: z.string().optional().nullable(), // Allow null or undefined for "None" option
  isActive: z.boolean().default(true),
});

export type PromptFormValues = z.infer<typeof promptFormSchema>;

interface PromptFormProps {
  onSave: (data: PromptFormValues) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  profiles: ProfileLike[];
  initialData?: PromptFormValues | null; // Optional prop for editing
}

export default function PromptForm({ onSave, onCancel, isSaving, profiles, initialData }: PromptFormProps) {
  const form = useForm<PromptFormValues>({
    resolver: zodResolver(promptFormSchema),
    defaultValues: initialData || {
      id: undefined,
      name: '',
      promptText: '',
      profileId: undefined,
      isActive: true,
    },
  });

  const { handleSubmit, control, watch, reset } = form; // Added reset
  const promptTextValue = watch("promptText", "");

  useEffect(() => {
    if (initialData) {
      reset(initialData);
    } else {
      // Reset to default empty values if creating a new prompt after editing
      reset({
        id: undefined,
        name: '',
        promptText: '',
        profileId: undefined,
        isActive: true,
      });
    }
  }, [initialData, reset]);

  const submitButtonText = initialData?.id ? "Save Changes" : "Save Prompt";

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit(onSave)} className="space-y-6 p-4">
        {/* ID field can be hidden if not needed in the form UI itself */}
        {/* <FormField control={control} name="id" render={({ field }) => <Input type="hidden" {...field} />} /> */}
        
        <FormField
          control={control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Prompt Name</FormLabel>
              <FormControl>
                <Input placeholder="e.g., Blog Post Idea Generator" {...field} />
              </FormControl>
              <FormDescription>
                A descriptive name for this AI prompt.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="promptText"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Prompt Text</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter your detailed AI prompt here..."
                  className="min-h-[150px] resize-y"
                  {...field}
                />
              </FormControl>
              <div className="flex justify-between items-center">
                <FormDescription>
                  The main content of your AI prompt.
                </FormDescription>
                <span className={`text-xs ${promptTextValue.length > MAX_PROMPT_LENGTH ? 'text-red-500' : 'text-muted-foreground'}`}>
                  {promptTextValue.length}/{MAX_PROMPT_LENGTH}
                </span>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={control}
          name="profileId"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Associated Profile (Optional)</FormLabel>
              <Select 
                onValueChange={(value) => field.onChange(value === "" ? null : value)} // Handle "None" selection
                value={field.value || ""} // Ensure value is controlled, fallback to empty string for "None"
                defaultValue={field.value || ""}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a profile (optional)" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {profiles.map(profile => (
                    <SelectItem key={profile.id} value={profile.id}>
                      {profile.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>
                Link this prompt to a specific bidding profile.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={control}
          name="isActive"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Active</FormLabel>
                <FormDescription>
                  Make this prompt available for use.
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

        <DrawerFooter className="pt-4 px-0">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSaving}>
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            {submitButtonText}
          </Button>
        </DrawerFooter>
      </form>
    </Form>
  );
}
