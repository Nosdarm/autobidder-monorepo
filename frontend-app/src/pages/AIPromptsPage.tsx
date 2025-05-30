import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '@/components/ui/table';
import { PlusCircle, Edit, Trash2, MoreHorizontal } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
// TODO: Import and use actual toast component, e.g., import { useToast } from "@/components/ui/use-toast";

// Mock data for AI Prompts
interface AIPrompt {
  id: string;
  name: string;
  prompt_text: string;
  category: 'General' | 'Marketing' | 'Technical' | 'Translation' | 'Content Generation';
  created_at: Date;
}

const mockAIPrompts: AIPrompt[] = [
  { id: '1', name: 'Blog Post Idea Generator', prompt_text: 'Generate 5 blog post ideas for a company that sells eco-friendly dog toys...', category: 'Marketing', created_at: new Date(2023, 10, 15) },
  { id: '2', name: 'Code Explainer', prompt_text: 'Explain the following Python code snippet in simple terms: ...', category: 'Technical', created_at: new Date(2023, 11, 1) },
  { id: '3', name: 'Email Subject Line Creator', prompt_text: 'Create 3 catchy email subject lines for a product launch announcement...', category: 'Marketing', created_at: new Date(2024, 0, 5) },
  { id: '4', name: 'French to English Translator', prompt_text: 'Translate the following text from French to English: ...', category: 'Translation', created_at: new Date(2024, 0, 20) },
  { id: '5', name: 'Product Description Writer', prompt_text: 'Write a 100-word product description for a new smart home device that...', category: 'Content Generation', created_at: new Date(2024, 1, 10) },
];

// Re-usable Card component (consider moving to a shared UI directory if not already there)
const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={`rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}
    {...props}
  />
);

export default function AIPromptsPage() {
  const { t } = useTranslation();
  // const { toast } = useToast(); // TODO: Uncomment when toast is available

  const [prompts, setPrompts] = useState<AIPrompt[]>(mockAIPrompts);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState<AIPrompt | null>(null);

  // Form state for the modal
  const [promptName, setPromptName] = useState('');
  const [promptCategory, setPromptCategory] = useState<'General' | 'Marketing' | 'Technical' | 'Translation' | 'Content Generation'>('General');
  const [promptText, setPromptText] = useState('');

  const handleOpenCreateModal = () => {
    setCurrentPrompt(null);
    setPromptName('');
    setPromptCategory('General');
    setPromptText('');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (prompt: AIPrompt) => {
    setCurrentPrompt(prompt);
    setPromptName(prompt.name);
    setPromptCategory(prompt.category);
    setPromptText(prompt.prompt_text);
    setIsModalOpen(true);
  };

  const handleOpenDeleteAlert = (prompt: AIPrompt) => {
    setCurrentPrompt(prompt);
    setIsDeleteAlertOpen(true);
  };

  const handleSavePrompt = () => {
    const newPromptData = {
      id: currentPrompt?.id || String(Date.now()), // Create new ID or use existing
      name: promptName,
      category: promptCategory,
      prompt_text: promptText,
      created_at: currentPrompt?.created_at || new Date(), // Preserve original or set new
    };
    console.log('Saving prompt:', newPromptData);
    // TODO: Show toast notification
    // toast({ title: t('aiPromptsPage.toast.saveSuccessTitle'), description: t('aiPromptsPage.toast.saveSuccessDescription', { name: newPromptData.name }) });
    alert(`Mock: Prompt "${newPromptData.name}" saved successfully!`); // Placeholder
    
    if (currentPrompt) {
      setPrompts(prompts.map(p => p.id === currentPrompt.id ? newPromptData : p));
    } else {
      setPrompts([...prompts, newPromptData]);
    }
    setIsModalOpen(false);
    setCurrentPrompt(null);
  };

  const handleConfirmDelete = () => {
    if (!currentPrompt) return;
    console.log('Deleting prompt ID:', currentPrompt.id);
    // TODO: Show toast notification
    // toast({ title: t('aiPromptsPage.toast.deleteSuccessTitle'), description: t('aiPromptsPage.toast.deleteSuccessDescription', { name: currentPrompt.name }) });
    alert(`Mock: Prompt "${currentPrompt.name}" deletion initiated!`); // Placeholder

    setPrompts(prompts.filter(p => p.id !== currentPrompt.id));
    setIsDeleteAlertOpen(false);
    setCurrentPrompt(null);
  };
  
  const modalTitle = currentPrompt 
    ? t('aiPromptsPage.editModal.title', 'Edit AI Prompt') 
    : t('aiPromptsPage.createModal.title', 'Create New AI Prompt');
  const modalDescription = currentPrompt 
    ? t('aiPromptsPage.editModal.description', 'Update the details for this AI prompt.')
    : t('aiPromptsPage.createModal.description', 'Fill in the details below to add a new AI prompt.');

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('aiPromptsPage.title', 'AI Prompts Management')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('aiPromptsPage.description', 'Manage your reusable AI prompts for various tasks.')}
          </p>
        </div>
        <Button onClick={handleOpenCreateModal}>
          <PlusCircle className="mr-2 h-4 w-4" /> {t('aiPromptsPage.createButton', 'Create New Prompt')}
        </Button>
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{modalTitle}</DialogTitle>
            <DialogDescription>{modalDescription}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">{t('aiPromptsPage.form.nameLabel', 'Name')}</Label>
              <Input id="name" value={promptName} onChange={(e) => setPromptName(e.target.value)} className="col-span-3" placeholder={t('aiPromptsPage.form.namePlaceholder', 'e.g., Blog Post Generator')} />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="category" className="text-right">{t('aiPromptsPage.form.categoryLabel', 'Category')}</Label>
              <Select value={promptCategory} onValueChange={(value: AIPrompt['category']) => setPromptCategory(value)}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder={t('aiPromptsPage.form.categoryPlaceholder', 'Select a category')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="General">{t('aiPromptsPage.form.categoryOptions.general', 'General')}</SelectItem>
                  <SelectItem value="Marketing">{t('aiPromptsPage.form.categoryOptions.marketing', 'Marketing')}</SelectItem>
                  <SelectItem value="Technical">{t('aiPromptsPage.form.categoryOptions.technical', 'Technical')}</SelectItem>
                  <SelectItem value="Translation">{t('aiPromptsPage.form.categoryOptions.translation', 'Translation')}</SelectItem>
                  <SelectItem value="Content Generation">{t('aiPromptsPage.form.categoryOptions.contentGeneration', 'Content Generation')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <Label htmlFor="prompt_text" className="text-right pt-2">{t('aiPromptsPage.form.promptTextLabel', 'Prompt Text')}</Label>
              <Textarea id="prompt_text" value={promptText} onChange={(e) => setPromptText(e.target.value)} className="col-span-3 min-h-[150px]" placeholder={t('aiPromptsPage.form.promptTextPlaceholder', 'Enter the full AI prompt here...')} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>{t('common.cancel', 'Cancel')}</Button>
            <Button type="submit" onClick={handleSavePrompt}>{t('aiPromptsPage.form.saveButton', 'Save Prompt')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Alert */}
      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('aiPromptsPage.deleteAlert.title', 'Confirm Deletion')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('aiPromptsPage.deleteAlert.description', { name: currentPrompt?.name || 'this prompt' })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setCurrentPrompt(null)}>{t('common.cancel', 'Cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-red-600 hover:bg-red-700">
              {t('common.confirmDeleteButton', 'Confirm Delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* AI Prompts Table */}
      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>{t('aiPromptsPage.table.caption', 'A list of your configured AI prompts.')}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[250px]">{t('aiPromptsPage.table.headerName', 'Name')}</TableHead>
              <TableHead>{t('aiPromptsPage.table.headerCategory', 'Category')}</TableHead>
              <TableHead>{t('aiPromptsPage.table.headerPromptSnippet', 'Prompt Snippet')}</TableHead>
              <TableHead>{t('aiPromptsPage.table.headerCreatedAt', 'Created At')}</TableHead>
              <TableHead className="text-right w-[120px]">{t('aiPromptsPage.table.headerActions', 'Actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {prompts.length > 0 ? prompts.map((prompt) => (
              <TableRow key={prompt.id}>
                <TableCell className="font-medium">{prompt.name}</TableCell>
                <TableCell>{prompt.category}</TableCell>
                <TableCell className="text-sm text-muted-foreground truncate max-w-xs">
                  {prompt.prompt_text.substring(0, 100)}{prompt.prompt_text.length > 100 ? '...' : ''}
                </TableCell>
                <TableCell>{format(prompt.created_at, 'PP')}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">{t('aiPromptsPage.table.actionsLabel', { name: prompt.name })}</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleOpenEditModal(prompt)}>
                        <Edit className="mr-2 h-4 w-4" />
                        {t('common.edit', 'Edit')}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleOpenDeleteAlert(prompt)} className="text-red-600 hover:!text-red-600 focus:text-red-600">
                        <Trash2 className="mr-2 h-4 w-4" />
                        {t('common.delete', 'Delete')}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  {t('aiPromptsPage.table.noPrompts', 'No AI prompts found. Get started by creating one!')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
