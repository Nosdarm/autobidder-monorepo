import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useToast } from '@/hooks/useToast';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next'; // Import useTranslation
import authService from '@/services/authService';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// Label is not directly used, FormLabel from ui/form is used.
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";

// Function to create schema with translated messages
const createRegisterSchema = (t: (key: string, params?: object) => string) => z.object({
  username: z.string()
    .nonempty({ message: t('auth.validation.usernameRequired') })
    .min(3, { message: t('auth.validation.usernameMinLength', { min: 3 }) }),
  email: z.string()
    .email({ message: t('auth.validation.invalidEmail') })
    .nonempty({ message: t('auth.validation.emailRequired') }),
  password: z.string()
    .nonempty({ message: t('auth.validation.passwordRequired') })
    .min(6, { message: t('auth.validation.passwordMinLength', { min: 6 }) }),
  confirmPassword: z.string()
    .nonempty({ message: t('auth.validation.confirmPasswordRequired') }),
}).refine(data => data.password === data.confirmPassword, {
  message: t('auth.validation.passwordsDoNotMatch'),
  path: ["confirmPassword"],
});

type RegisterFormValues = z.infer<ReturnType<typeof createRegisterSchema>>;

export default function RegisterPage() {
  const { t } = useTranslation(); // Initialize useTranslation
  const navigate = useNavigate();
  const { showToastSuccess, showToastError } = useToast();
  const registerSchema = createRegisterSchema(t); // Create schema with t function

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const {
    handleSubmit,
    formState: { isSubmitting },
  } = form;

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      await authService.register({
        name: data.username,
        email: data.email,
        password: data.password,
      });
      showToastSuccess(t('auth.register.registrationSuccess'));
      navigate('/login');
    } catch (error: any) {
      showToastError(error.message || t('auth.register.registrationErrorDefault'));
      console.error("Registration error", error);
    }
  };

  return (
    <Card className="w-full sm:w-96 mx-auto mt-24">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">{t('auth.register.title')}</CardTitle>
        <CardDescription>{t('auth.register.description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('auth.register.usernameLabel')}</FormLabel>
                  <FormControl>
                    <Input placeholder={t('auth.register.usernamePlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('auth.register.emailLabel')}</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder={t('auth.register.emailPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('auth.register.passwordLabel')}</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder={t('auth.register.passwordPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('auth.register.confirmPasswordLabel')}</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder={t('auth.register.confirmPasswordPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t('auth.register.registerButton')}
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex flex-col items-center space-y-2">
        <p className="text-sm text-muted-foreground">
          {t('auth.register.loginPrompt')}{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            {t('auth.register.loginLink')}
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
