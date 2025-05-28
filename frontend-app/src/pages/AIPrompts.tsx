import React, { useState } from 'react';
import { format } from 'date-fns';
import { PlusCircle, MoreHorizontal, Edit, Trash2, Eye, Loader2 as SpinnerIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next'; // Import useTranslation

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
  DialogFooter,
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton'; 

import PromptForm, { PromptFormValues } from '@/components/ai/PromptForm';
import { 
  useAIPrompts, 
  useCreateAIPrompt, 
  useUpdateAIPrompt, 
  useDeleteAIPrompt, 
  usePreviewAIPrompt 
} from '@/hooks/useAIPromptQueries';
import { AIPrompt } from '@/services/aiPromptService'; 
import { useToast } from '@/hooks/useToast'; 

// Mock Profile Data - To be replaced with actual profile data fetching later
interface ProfileLike {
  id: string;
  name: string;
}
const mockProfilesForSelect: ProfileLike[] = [
  { id: '1', name: 'My Upwork Freelancer' },
  { id: '2', name: 'Agency Client X' },
  { id: '3', name: 'Test Profile Alpha' },
];

export default function AIPromptsPage() {
  const { t } = useTranslation(); // Initialize useTranslation
  const { data: prompts, isLoading: isLoadingPrompts, error: promptsError } = useAIPrompts();
  const { showToastSuccess } = useToast(); 
  
  const createPromptMutation = useCreateAIPrompt();
  const updatePromptMutation = useUpdateAIPrompt();
  const deletePromptMutation = useDeleteAIPrompt();
  const previewPromptMutation = usePreviewAIPrompt();

  const [isCreateDrawerOpen, setIsCreateDrawerOpen] = useState(false);
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [promptToEdit, setPromptToEdit] = useState<AIPrompt | null>(null);
  
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [promptToDelete, setPromptToDelete] = useState<AIPrompt | null>(null);
  
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [promptToPreview, setPromptToPreview] = useState<AIPrompt | null>(null);
  const [previewInputText, setPreviewInputText] = useState('');
  const [previewOutputText, setPreviewOutputText] = useState('');

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
    setPreviewInputText('');
    setPreviewOutputText('');
    setIsPreviewDialogOpen(true);
  };

  const handleSavePrompt = async (data: PromptFormValues) => {
    const promptData = {
      ...data,
      profileId: data.profileId || null, 
    };

    if (data.id) { 
      updatePromptMutation.mutate(
        { id: data.id, data: promptData },
        {
          onSuccess: () => {
            setIsEditDrawerOpen(false);
            setPromptToEdit(null);
          }
        }
      );
    } else { 
      createPromptMutation.mutate(
        promptData,
        {
          onSuccess: () => {
            setIsCreateDrawerOpen(false);
          }
        }
      );
    }
  };
  
  const handleConfirmDelete = async () => {
    if (!promptToDelete) return;
    deletePromptMutation.mutate(promptToDelete.id, {
      onSuccess: () => {
        setIsDeleteAlertOpen(false);
        setPromptToDelete(null);
      }
    });
  };

  const handleGeneratePreview = async () => {
    if (!promptToPreview) return;
    setPreviewOutputText(''); 
    previewPromptMutation.mutate(
      { promptText: promptToPreview.promptText, testInput: previewInputText },
      {
        onSuccess: (data) => {
          setPreviewOutputText(data.previewText || t('aiPrompts.previewDialog.noPreviewGenerated'));
          showToastSuccess(t('aiPrompts.previewDialog.previewGeneratedSuccess')); 
        },
      }
    );
  };

  const isSavingPrompt = createPromptMutation.isPending || updatePromptMutation.isPending;
  const isDeletingPrompt = deletePromptMutation.isPending;
  const isPreviewLoading = previewPromptMutation.isPending;

  if (promptsError) {
    return (
      <div className="p-4 md:p-6 text-red-600">
        {t('aiPrompts.errorLoading', { errorMessage: promptsError.message })}
      </div>
    );
  }

  const currentDrawerPromptData = promptToEdit ? promptToEdit : undefined;
  const drawerOpenState = isCreateDrawerOpen || isEditDrawerOpen;
  const setDrawerOpenState = (isOpen: boolean) => {
      if (isCreateDrawerOpen && !isOpen) setIsCreateDrawerOpen(false);
      if (isEditDrawerOpen && !isOpen) setIsEditDrawerOpen(false);
  };
  
  // Dynamic drawer titles and descriptions
  const drawerTitle = promptToEdit 
    ? t('aiPrompts.drawer.editTitle') 
    : t('aiPrompts.drawer.createTitle');
  const drawerDescription = promptToEdit 
    ? t('aiPrompts.drawer.editDescription') 
    : t('aiPrompts.drawer.createDescription');

  const getProfileNameById = (profileId?: string | null) => {
    if (!profileId) return t('aiPrompts.status.noProfileAssociated'); // N/A
    return mockProfilesForSelect.find(p => p.id === profileId)?.name || t('aiPrompts.status.unknownProfile');
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('aiPrompts.title')}</h1>
          <p className="text-sm text-muted-foreground">{t('aiPrompts.description')}</p>
        </div>
        <Button onClick={handleOpenCreateDrawer}>
          <PlusCircle className="mr-2 h-4 w-4" /> {t('aiPrompts.createPrompt')}
        </Button>
      </div>

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

      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('aiPrompts.deleteDialog.title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('aiPrompts.deleteDialog.areYouSure', { promptName: promptToDelete?.name || '' })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPromptToDelete(null)} disabled={isDeletingPrompt}>
              {t('aiPrompts.deleteDialog.cancel')}
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmDelete} 
              disabled={isDeletingPrompt}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeletingPrompt ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t('aiPrompts.deleteDialog.confirmDelete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={isPreviewDialogOpen} onOpenChange={setIsPreviewDialogOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{t('aiPrompts.previewDialog.title', { promptName: promptToPreview?.name || '' })}</DialogTitle>
            <DialogDescription>
              {t('aiPrompts.previewDialog.description')}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="preview-input" className="text-sm font-medium">
                {t('aiPrompts.previewDialog.testInputLabel')}
              </Label>
              <Textarea
                id="preview-input"
                placeholder={t('aiPrompts.previewDialog.testInputPlaceholder')}
                value={previewInputText}
                onChange={(e) => setPreviewInputText(e.target.value)}
                className="mt-1 min-h-[100px]"
              />
            </div>
            <Button onClick={handleGeneratePreview} disabled={isPreviewLoading} className="w-full">
              {isPreviewLoading ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> : <Eye className="mr-2 h-4 w-4" />}
              {t('aiPrompts.previewDialog.generatePreview')}
            </Button>
            {previewOutputText && (
              <div className="mt-4 space-y-2">
                <Label className="text-sm font-medium">{t('aiPrompts.previewDialog.generatedOutputLabel')}</Label>
                <div className="p-3 bg-muted rounded-md text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {previewOutputText}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPreviewDialogOpen(false)}>
              {t('aiPrompts.previewDialog.close')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>{t('aiPrompts.table.caption')}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[250px]">{t('aiPrompts.table.headerName')}</TableHead>
              <TableHead>{t('aiPrompts.table.headerProfile')}</TableHead>
              <TableHead>{t('aiPrompts.table.headerActive')}</TableHead>
              <TableHead>{t('aiPrompts.table.headerCreatedAt')}</TableHead>
              <TableHead className="text-right w-[100px]">{t('aiPrompts.table.headerActions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoadingPrompts ? (
              Array.from({ length: 3 }).map((_, index) => ( 
                <TableRow key={`skeleton-${index}`}>
                  <TableCell><Skeleton className="h-5 w-3/4" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-1/2" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-1/4" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-1/2" /></TableCell>
                  <TableCell className="text-right"><Skeleton className="h-8 w-8 inline-block" /></TableCell>
                </TableRow>
              ))
            ) : (prompts && prompts.length > 0) ? (
              prompts.map((prompt) => (
                <TableRow key={prompt.id}>
                  <TableCell className="font-medium">{prompt.name}</TableCell>
                  <TableCell>{getProfileNameById(prompt.profileId)}</TableCell>
                  <TableCell>
                    <Badge variant={prompt.isActive ? 'default' : 'outline'}
                           className={prompt.isActive ? 'bg-green-500 hover:bg-green-600' : ''}>
                      {prompt.isActive ? t('aiPrompts.status.activeYes') : t('aiPrompts.status.activeNo')}
                    </Badge>
                  </TableCell>
                  <TableCell>{format(new Date(prompt.createdAt), 'PPp')}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">{t('aiPrompts.actions.openMenuFor', { promptName: prompt.name })}</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>{t('aiPrompts.actions.label')}</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => handleOpenEditDrawer(prompt)}>
                          <Edit className="mr-2 h-4 w-4" /> {t('aiPrompts.actions.edit')}
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleOpenPreviewDialog(prompt)}>
                          <Eye className="mr-2 h-4 w-4" /> {t('aiPrompts.actions.preview')}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => handleOpenDeleteAlert(prompt)} 
                          className="text-red-600 hover:!text-red-600 focus:text-red-600"
                          disabled={deletePromptMutation.isPending && promptToDelete?.id === prompt.id}
                        >
                          {deletePromptMutation.isPending && promptToDelete?.id === prompt.id 
                            ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> 
                            : <Trash2 className="mr-2 h-4 w-4" />}
                           {t('aiPrompts.actions.delete')}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  {isLoadingPrompts ? t('aiPrompts.loading') : t('aiPrompts.table.noPrompts')}
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
