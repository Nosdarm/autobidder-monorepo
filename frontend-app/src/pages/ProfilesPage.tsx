import React, { useState } from 'react';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';
import { PlusCircle, MoreHorizontal, Edit, Trash2, Loader2 as SpinnerIcon, AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
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

import ProfileCreateForm, { ProfileFormValues } from '@/components/profiles/ProfileCreateForm';
import { 
  useProfiles, 
  useCreateProfile, 
  useUpdateProfile, 
  useDeleteProfile 
} from '@/hooks/useProfileQueries';
import type { Profile } from '@/services/profileService';


export default function ProfilesPage() {
  const { t } = useTranslation();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [profileToEdit, setProfileToEdit] = useState<Profile | null>(null);
  
  const [isDeleteAlertOpen, setIsDeleteAlertOpen] = useState(false);
  const [profileToDelete, setProfileToDelete] = useState<Profile | null>(null);

  const { data: profiles = [], isLoading, isError, error } = useProfiles();
  const createProfileMutation = useCreateProfile();
  const updateProfileMutation = useUpdateProfile();
  const deleteProfileMutation = useDeleteProfile();

  const handleOpenCreateModal = () => {
    setProfileToEdit(null);
    setIsCreateModalOpen(true);
  };

  const handleOpenEditModal = (profile: Profile) => {
    const profileWithDate = { ...profile, createdAt: new Date(profile.createdAt) };
    setProfileToEdit(profileWithDate);
    setIsEditModalOpen(true);
  };

  const handleOpenDeleteAlert = (profile: Profile) => {
    setProfileToDelete(profile);
    setIsDeleteAlertOpen(true);
  };

  const handleSaveProfile = async (formData: ProfileFormValues) => {
    try {
      if (formData.id) {
        await updateProfileMutation.mutateAsync({ id: formData.id, data: formData });
      } else {
        const { id, ...newProfileData } = formData;
        await createProfileMutation.mutateAsync(newProfileData);
      }
      setIsCreateModalOpen(false);
      setIsEditModalOpen(false);
    } catch (e) {
      console.error("Failed to save profile:", e);
    }
  };
  
  const handleConfirmDelete = async () => {
    if (!profileToDelete) return;
    try {
      await deleteProfileMutation.mutateAsync(profileToDelete.id);
      setIsDeleteAlertOpen(false);
      setProfileToDelete(null);
    } catch (e) {
      console.error("Failed to delete profile:", e);
    }
  };

  const currentModalProfileData = profileToEdit 
    ? { 
        id: profileToEdit.id, 
        name: profileToEdit.name, 
        type: profileToEdit.type, 
        autobidEnabled: profileToEdit.autobidEnabled 
      } 
    : undefined;

  const modalOpenState = isCreateModalOpen || isEditModalOpen;
  const setModalOpenState = (isOpen: boolean) => {
      if (!isOpen) {
          setIsCreateModalOpen(false);
          setIsEditModalOpen(false);
          setProfileToEdit(null);
      }
  };
  
  const modalTitle = profileToEdit 
    ? t('profilesPage.editModalTitle') 
    : t('profilesPage.createModalTitle');
  const modalDescription = profileToEdit 
    ? t('profilesPage.editModalDescription')
    : t('profilesPage.createModalDescription');

  if (isLoading) {
    return (
      <div className="p-4 md:p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{t('profilesPage.title')}</h1>
          <Skeleton className="h-10 w-36" /> {/* Button Skeleton */}
        </div>
        <Card className="border shadow-sm rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                {[...Array(5)].map((_, i) => <TableHead key={i}><Skeleton className="h-5 w-full" /></TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...Array(3)].map((_, i) => (
                <TableRow key={i}>
                  {[...Array(5)].map((_, j) => <TableCell key={j}><Skeleton className="h-5 w-full" /></TableCell>)}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 md:p-6 text-center">
        <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
        <h2 className="mt-4 text-xl font-semibold text-red-600">{t('profilesPage.error.title')}</h2>
        <p className="mt-2 text-muted-foreground">
          {error?.message || t('profilesPage.error.defaultMessage')}
        </p>
      </div>
    );
  }
  
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
            <h1 className="text-2xl font-semibold">{t('profilesPage.title')}</h1>
          <p className="text-sm text-muted-foreground">
              {t('profilesPage.description')}
          </p>
        </div>
        <Button onClick={handleOpenCreateModal}>
            <PlusCircle className="mr-2 h-4 w-4" /> {t('profilesPage.createProfileButton')}
        </Button>
      </div>

      <Dialog open={modalOpenState} onOpenChange={setModalOpenState}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{modalTitle}</DialogTitle>
            <DialogDescription>{modalDescription}</DialogDescription>
          </DialogHeader>
          <ProfileCreateForm
            onSave={handleSaveProfile}
            onCancel={() => setModalOpenState(false)}
            isSaving={createProfileMutation.isPending || updateProfileMutation.isPending}
            initialData={currentModalProfileData}
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setIsDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('profilesPage.deleteAlertTitle')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('profilesPage.deleteAlertDescription', { profileName: profileToDelete?.name })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setProfileToDelete(null)} disabled={deleteProfileMutation.isPending}>
              {t('profileForm.cancelButton')}
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmDelete} 
              disabled={deleteProfileMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {deleteProfileMutation.isPending ? <SpinnerIcon className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t('common.confirmDeleteButton')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>{t('profilesPage.tableCaption')}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">{t('profilesPage.tableHeaderName')}</TableHead>
              <TableHead>{t('profilesPage.tableHeaderType')}</TableHead>
              <TableHead>{t('profilesPage.tableHeaderAutobid')}</TableHead>
              <TableHead>{t('profilesPage.tableHeaderCreatedAt')}</TableHead>
              <TableHead className="text-right w-[100px]">{t('profilesPage.tableHeaderActions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {profiles && profiles.length > 0 ? (
              profiles.map((profile) => (
                <TableRow key={profile.id}>
                  <TableCell className="font-medium">{profile.name}</TableCell>
                  <TableCell>
                    <Badge variant={profile.type === 'agency' ? 'secondary' : 'outline'}>
                      {profile.type.charAt(0).toUpperCase() + profile.type.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={profile.autobidEnabled ? 'default' : 'destructive'} 
                           className={profile.autobidEnabled ? 'bg-green-500 hover:bg-green-600' : ''}>
                      {profile.autobidEnabled ? t('common.enabled') : t('common.disabled')}
                    </Badge>
                  </TableCell>
                  <TableCell>{format(new Date(profile.createdAt), 'PPpp')}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">{t('profilesPage.actions.openMenuFor', { profileName: profile.name })}</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>{t('common.actions')}</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => handleOpenEditModal(profile)}>
                          <Edit className="mr-2 h-4 w-4" />
                          {t('profilesPage.actions.editProfile')}
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleOpenDeleteAlert(profile)} className="text-red-600 hover:!text-red-600 focus:text-red-600">
                          <Trash2 className="mr-2 h-4 w-4" />
                          {t('profilesPage.actions.deleteProfile')}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem disabled> 
                          {t('common.viewAutobidLogs')}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  {t('profilesPage.noProfilesFound')}
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
