import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '@/components/ui/table';
import { PlusCircle, Edit, Trash2, AlertTriangle } from 'lucide-react';
// TODO: Import toast once implemented or available e.g. import { useToast } from "@/components/ui/use-toast";

// Mock data for team members (can be moved to a separate file later)
interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'Admin' | 'Member';
}

const mockTeamMembers: TeamMember[] = [
  { id: '1', name: 'Alice Wonderland', email: 'alice@example.com', role: 'Admin' },
  { id: '2', name: 'Bob The Builder', email: 'bob@example.com', role: 'Member' },
  { id: '3', name: 'Charlie Brown', email: 'charlie@example.com', role: 'Member' },
];

export default function TeamPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  // const { toast } = useToast(); // TODO: Uncomment when toast is available

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'Admin' | 'Member'>('Member');

  if (!user || user.account_type !== 'agency') {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center" data-cy="team-page-access-denied-message">
        <AlertTriangle className="w-16 h-16 text-yellow-500 mb-4" />
        <h1 className="text-2xl font-semibold mb-2">{t('teamPage.accessDenied.title', 'Access Denied')}</h1>
        <p className="text-muted-foreground">
          {t('teamPage.accessDenied.description', 'This page is only accessible to Agency accounts.')}
        </p>
        {/* TODO: Role-based UI - Consider if the entire page view should be different for a non-admin member, e.g., view-only mode or fewer details. */}
      </div>
    );
  }

  const handleSendInvitation = () => {
    console.log('Sending invitation to:', inviteEmail, 'with role:', inviteRole);
    // TODO: Show toast notification
    // toast({
    //   title: t('teamPage.inviteModal.toastSuccessTitle', 'Invitation Sent'),
    //   description: t('teamPage.inviteModal.toastSuccessDescription', { email: inviteEmail }),
    // });
    alert(`Mock: Invitation sent to ${inviteEmail} with role ${inviteRole}`); // Placeholder for toast
    setIsInviteModalOpen(false);
    setInviteEmail('');
    setInviteRole('Member');
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" data-cy="team-page-title">{t('teamPage.title', 'Team Management')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('teamPage.description', 'Manage your team members and their roles.')}
          </p>
        </div>
        <Dialog open={isInviteModalOpen} onOpenChange={setIsInviteModalOpen}>
          <DialogTrigger asChild>
            {/* TODO: Role-based access - This button should likely only be visible to 'Admin' or 'Super Admin' roles within the agency. */}
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> {t('teamPage.inviteButton', 'Invite New Member')}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            {/* TODO: Role-based UI - The roles available in the invite modal (e.g., 'Admin', 'Member') 
                might be restricted based on the inviting user's role. 
                A 'Super Admin' might be able to create 'Admin' users, but an 'Admin' might only be able to create 'Member' users. */}
            <DialogHeader>
              <DialogTitle>{t('teamPage.inviteModal.title', 'Invite New Member')}</DialogTitle>
              <DialogDescription>
                {t('teamPage.inviteModal.description', 'Enter the email and role for the new team member.')}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="email" className="text-right">
                  {t('teamPage.inviteModal.emailLabel', 'Email')}
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="col-span-3"
                  placeholder="name@example.com"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="role" className="text-right">
                  {t('teamPage.inviteModal.roleLabel', 'Role')}
                </Label>
                {/* TODO: Role-based UI - Options in this Select might be filtered based on the current user's role.
                    For example, an 'Admin' might not be able to create another 'Admin'. */}
                <Select value={inviteRole} onValueChange={(value: 'Admin' | 'Member') => setInviteRole(value)}>
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder={t('teamPage.inviteModal.rolePlaceholder', 'Select a role')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Member">{t('teamPage.inviteModal.roleMember', 'Member')}</SelectItem>
                    <SelectItem value="Admin">{t('teamPage.inviteModal.roleAdmin', 'Admin')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsInviteModalOpen(false)}>
                {t('common.cancel', 'Cancel')}
              </Button>
              {/* TODO: Role-based access - The ability to send an invitation might be disabled if certain conditions aren't met (e.g. trying to invite an Admin as a Member) */}
              <Button type="submit" onClick={handleSendInvitation}>
                {t('teamPage.inviteModal.sendButton', 'Send Invitation')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Team Members Table */}
      <Card className="border shadow-sm rounded-lg">
        <Table>
          <TableCaption>{t('teamPage.membersTable.caption', 'A list of your team members.')}</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>{t('teamPage.membersTable.headerName', 'Name')}</TableHead>
              <TableHead>{t('teamPage.membersTable.headerEmail', 'Email')}</TableHead>
              <TableHead>{t('teamPage.membersTable.headerRole', 'Role')}</TableHead>
              <TableHead className="text-right">{t('teamPage.membersTable.headerActions', 'Actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockTeamMembers.map((member) => (
              <TableRow key={member.id}>
                <TableCell className="font-medium">{member.name}</TableCell>
                <TableCell>{member.email}</TableCell>
                <TableCell>{member.role}</TableCell>
                <TableCell className="text-right space-x-2">
                  {/* TODO: Role-based access - Edit/Remove actions might be restricted.
                      - Users might not be able to edit/remove themselves.
                      - 'Member' role might not be able to edit/remove anyone.
                      - 'Admin' might only edit/remove 'Member' roles, or other 'Admin' roles if not 'Super Admin' protected.
                      - Visibility of these buttons will depend on these rules.
                  */}
                  <Button variant="outline" size="sm" disabled> {/* 'disabled' is placeholder for actual role check */}
                    <Edit className="mr-1 h-3 w-3" /> {t('common.edit', 'Edit')}
                  </Button>
                  <Button variant="outline" size="sm" disabled className="text-red-600 hover:text-red-700"> {/* 'disabled' is placeholder */}
                    <Trash2 className="mr-1 h-3 w-3" /> {t('common.delete', 'Remove')}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

// Re-usable Card component (consider moving to a shared UI directory if not already there)
// For now, defining it locally to make the page self-contained for this step.
const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={`rounded-lg border bg-card text-card-foreground shadow-sm ${className}`}
    {...props}
  />
);
