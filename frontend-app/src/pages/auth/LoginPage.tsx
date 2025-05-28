import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useToast } from '@/hooks/useToast';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next'; // Import useTranslation

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
// Label is not directly used, FormLabel from ui/form is used.
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";

// Function to create schema with translated messages
const createLoginSchema = (t: (key: string) => string) => z.object({
  email: z.string()
    .email({ message: t('auth.validation.invalidEmail') })
    .nonempty({ message: t('auth.validation.emailRequired') }),
  password: z.string()
    .nonempty({ message: t('auth.validation.passwordRequired') }),
});

type LoginFormValues = z.infer<ReturnType<typeof createLoginSchema>>;

export default function LoginPage() {
  const { t } = useTranslation(); // Initialize useTranslation
  const navigate = useNavigate();
  const { showToastError, showToastSuccess } = useToast(); // Added showToastSuccess for completeness
  const loginSchema = createLoginSchema(t); // Create schema with t function

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const {
    handleSubmit,
    formState: { isSubmitting },
  } = form;

  const onSubmit = async (data: LoginFormValues) => {
    console.log("Form submitted with data:", data);
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      // Placeholder for actual login logic
      // Simulate a success for demonstration, then switch to error
      if (data.email === "success@example.com") {
        showToastSuccess(t('auth.login.loginSuccess'));
        navigate('/dashboard');
      } else {
        throw new Error(t('auth.login.loginErrorDefault'));
      }
    } catch (error: any) {
      showToastError(error.message || t('auth.login.loginErrorDefault'));
      console.error("Login error", error);
    }
  };

  return (
    <Card className="w-full sm:w-96 mx-auto mt-24">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">{t('auth.login.title')}</CardTitle>
        <CardDescription>{t('auth.login.description')}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('auth.login.emailLabel')}</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder={t('auth.login.emailPlaceholder')} {...field} />
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
                  <FormLabel>{t('auth.login.passwordLabel')}</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder={t('auth.login.passwordPlaceholder')} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t('auth.login.loginButton')}
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex flex-col items-center space-y-2">
        <p className="text-sm text-muted-foreground">
          {t('auth.login.signupPrompt')}{' '}
          <Link to="/auth/register" className="font-medium text-primary hover:underline">
            {t('auth.login.signupLink')}
          </Link>
        </p>
        {/* 
        <p className="text-sm text-muted-foreground">
          <Link to="/auth/forgot-password" className="font-medium text-primary hover:underline">
            {t('auth.login.forgotPasswordLink')}
          </Link>
        </p>
        */}
      </CardFooter>
    </Card>
  );
}
