import React, { useState } from 'react';
import { format } from 'date-fns';
import { PlusCircle, MoreHorizontal, Edit, Trash2, Eye, Loader2 as SpinnerIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '@/components/ui/table';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter, // For Preview Dialog
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Textarea } from '@/components/ui/textarea'; // For Preview Dialog
import { Label } from '@/components/ui/label'; // For Preview Dialog
import toast from 'react-hot-toast';

import PromptForm, { PromptFormValues } from '@/components/ai/PromptForm';

// AI Prompt Data Interface
interface AIPrompt {
  id: string;
  name: string;
  promptText: string;
  profileId?: string | null; // Allow null
  isActive: boolean;
  createdAt: Date;
}

// Mock Profile Data
interface ProfileLike {
  id: string;
  name: string;
}
const mockProfilesForSelect: ProfileLike[] = [
  { id: '1', name: 'My Upwork Freelancer' },
  { id: '2', name: 'Agency Client X' },
  { id: '3', name: 'Test Profile Alpha' },
];

const mockAIPrompts: AIPrompt[] = [
  { id: 'p1', name: 'Cover Letter Intro', promptText: 'Write a compelling opening paragraph for a cover letter for a {JOB_TITLE} role focusing on {SKILL_1} and {SKILL_2}. The company is {COMPANY_NAME}.', profileId: '1', isActive: true, createdAt: new Date(2023, 10, 20) },
  { id: 'p2', name: 'Project Summary Generator', promptText: 'Summarize a project based on the following key points: {KEY_POINTS}. The project goal was {PROJECT_GOAL}.', isActive: false, createdAt: new Date(2023, 11, 5) },
  { id: 'p3', name: 'Follow-up Email Template', promptText: 'Draft a polite follow-up email after a job application for {JOB_TITLE} at {COMPANY_NAME}. Mention interest in {SPECIFIC_ASPECT}.', profileId: '2', isActive: true, createdAt: new Date() },
];

export default function AIPromptsPage() {
  const [prompts, setPrompts] = useState<AIPrompt[]>(mockAIPrompts);
  
  const [isCreateDrawerOpen, setIsCreateDrawerOpen] = useState(false);
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [promptToEdit, setPromptToEdit] = useState<AIPrompt | null>(null);
  
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [promptToDelete, setPromptToDelete] = useState<AIPrompt | null>(null);
  
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [promptToPreview, setPromptToPreview] = useState<AIPrompt | null>(null);
  const [previewInputText, setPreviewInputText] = useState('');
  const [previewOutputText, setPreviewOutputText] = useState('');
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const [isSavingPrompt, setIsSavingPrompt] = useState(false);
  const [isDeletingPrompt, setIsDeletingPrompt] = useState(false);

  const isLoading = false; // Mock page loading state

  const handleOpenCreateDrawer = () => {
    setPromptToEdit(null);
    setIsCreateDrawerOpen(true);
  };

  const handleOpenEditDrawer = (prompt: AIPrompt) => {
    setPromptToEdit(prompt);
    setIsEditDrawerOpen(true);
  };

  const handleOpenDeleteAlert = (prompt: AIPrompt) => {
    setPromptToDelete(prompt);
    setIsDeleteAlertOpen(true);
  };
  
  const handleOpenPreviewDialog = (prompt: AIPrompt) => {
    setPromptToPreview(prompt);
    setPreviewInputText(''); // Reset input/output for new preview
    setPreviewOutputText('');
    setIsPreviewDialogOpen(true);
  };

  const handleSavePrompt = async (data: PromptFormValues) => {
    setIsSavingPrompt(true);
    console.log('Saving AI prompt with data:', data);
    await new Promise(resolve => setTimeout(resolve, 1500));

    if (data.id) { // Editing existing prompt
      setPrompts(prevPrompts => prevPrompts.map(p => p.id === data.id ? { ...p, ...data, promptText: data.promptText, profileId: data.profileId } as AIPrompt : p));
      toast.success(`Prompt "${data.name}" updated successfully!`);
    } else { // Creating new prompt
      const newPrompt: AIPrompt = {
        ...data,
        id: String(Date.now()),
        createdAt: new Date(),
        promptText: data.promptText,
        profileId: data.profileId,
      };
      setPrompts(prevPrompts => [...prevPrompts, newPrompt]);
      toast.success(`Prompt "${data.name}" created successfully!`);
    }

    setIsSavingPrompt(false);
    setIsCreateDrawerOpen(false);
    setIsEditDrawerOpen(false);
  };
  
  const handleConfirmDelete = async () => {
    if (!promptToDelete) return;
    setIsDeletingPrompt(true);
    console.log('Deleting AI prompt with ID:', promptToDelete.id);
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setPrompts(prevPrompts => prevPrompts.filter(p => p.id !== promptToDelete.id));
    toast.success(`Prompt "${promptToDelete.name}" deleted successfully!`);

    setIsDeletingPrompt(false);
    setIsDeleteAlertOpen(false);
    setPromptToDelete(null);
  };

  const handleGeneratePreview = async () => {
    if (!promptToPreview) return;
    setIsPreviewLoading(true);
    setPreviewOutputText('');
    console.log('Generating preview for prompt:', promptToPreview.name, 'with input:', previewInputText);
    // Simulate AI generation
    await new Promise(resolve => setTimeout(resolve, 1500));
    // Replace placeholders in prompt text with input. A more robust replacement is needed for real use.
    let generated = promptToPreview.promptText.replace(/{[^{}]+}/g, `[${previewInputText || 'TEST_INPUT'}]`);
    generated += `\n\n--- (Simulated AI Output using input: "${previewInputText}") ---`;
    setPreviewOutputText(generated);
    setIsPreviewLoading(false);
  };

  if (isLoading) {
    return <div>Loading AI prompts...</div>;
  }

  const currentDrawerPromptData = promptToEdit ? promptToEdit : undefined;
  const drawerOpenState = isCreateDrawerOpen || isEditDrawerOpen;
  const setDrawerOpenState = (isOpen: boolean) => {
      if (isCreateDrawerOpen && !isOpen) setIsCreateDrawerOpen(false);
      if (isEditDrawerOpen && !isOpen) setIsEditDrawerOpen(false);
  };
  const drawerTitle = promptToEdit ? "Edit AI Prompt" : "Create New AI Prompt";
  const drawerDescription = promptToEdit 
    ? "Update the details for this AI prompt." 
    : "Fill in the details below to add a new AI prompt.";

  const getProfileNameById = (profileId?: string | null) => {
    if (!profileId) return 'N/A';
    return mockProfilesForSelect.find(p => p.id === profileId)?.name || 'Unknown Profile';
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">AI Prompts Library</h1>
          <p className="text-sm text-muted-foreground">Manage your reusable AI prompts.</p>
        </div>
        <Button onClick={handleOpenCreateDrawer}>
          <PlusCircle className="mr-2 h-4 w-4" /> Create Prompt
        </Button>
      </div>

      {/* Create/Edit Prompt Drawer */}
      <Drawer open={drawerOpenState} onOpenChange={setDrawerOpenState}>
        <DrawerContent>
          <div className="mx-auto w-full max-w-2xl">
            <DrawerHeader className="pt-6 px-4">
              <DrawerTitle>{drawerTitle}</DrawerTitle>
              <DrawerDescription>{drawerDescription}</DrawerDescription>
            </DrawerHeader>
            <div className="overflow-y-auto max-h-[calc(100vh-160px)]">
              <PromptForm
                onSave={handleSavePrompt}
                onCancel={() => setDrawerOpenState(false)}
                isSaving={isSavingPrompt}
                profiles={mockProfilesForSelect}
                initialData={currentDrawerPromptData}
              />
            </div>
          </div>
        </DrawerContent>
      </Drawer>

      {/* Delete Prompt Alert Dialog */}
      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Deletion</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete prompt "{promptToDelete?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPromptToDelete(null)} disabled={isDeletingPrompt}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmDelete} 
              disabled={isDeletingPrompt}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeletingPrompt ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> : null}
              Confirm Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Preview Prompt Dialog */}
      <Dialog open={isPreviewDialogOpen} onOpenChange={setIsPreviewDialogOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Preview AI Prompt: {promptToPreview?.name}</DialogTitle>
            <DialogDescription>
              Enter text below to test the selected prompt. Placeholders like `{{'{PLACEHOLDER_NAME}'}}` in the prompt will be simulated.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="preview-input" className="text-sm font-medium">Test Input (e.g., Vacancy Description)</Label>
              <Textarea
                id="preview-input"
                placeholder="Paste relevant text here to test the prompt..."
                value={previewInputText}
                onChange={(e) => setPreviewInputText(e.target.value)}
                className="mt-1 min-h-[100px]"
              />
            </div>
            <Button onClick={handleGeneratePreview} disabled={isPreviewLoading} className="w-full">
              {isPreviewLoading ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> : null}
              Generate Preview
            </Button>
            {previewOutputText && (
              <div className="mt-4 space-y-2">
                <Label className="text-sm font-medium">Generated Output</Label>
                <div className="p-3 bg-muted rounded-md text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {previewOutputText}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPreviewDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Prompts Table */}
      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>A list of your configured AI prompts.</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[250px]">Name</TableHead>
              <TableHead>Associated Profile</TableHead>
              <TableHead>Active</TableHead>
              <TableHead className="text-right w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {prompts.length > 0 ? (
              prompts.map((prompt) => (
                <TableRow key={prompt.id}>
                  <TableCell className="font-medium">{prompt.name}</TableCell>
                  <TableCell>{getProfileNameById(prompt.profileId)}</TableCell>
                  <TableCell>
                    <Badge variant={prompt.isActive ? 'default' : 'outline'}
                           className={prompt.isActive ? 'bg-green-500 hover:bg-green-600' : ''}>
                      {prompt.isActive ? 'Yes' : 'No'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => handleOpenEditDrawer(prompt)}>
                          <Edit className="mr-2 h-4 w-4" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleOpenPreviewDialog(prompt)}>
                          <Eye className="mr-2 h-4 w-4" /> Preview
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleOpenDeleteAlert(prompt)} className="text-red-600 hover:!text-red-600 focus:text-red-600">
                          <Trash2 className="mr-2 h-4 w-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center">
                  No AI prompts found. Get started by creating one!
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={`rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}
    {...props}
  />
);
