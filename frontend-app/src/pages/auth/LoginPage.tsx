import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
// import toast from 'react-hot-toast'; // Replaced by useToast
import { useToast } from '@/hooks/useToast'; // Import useToast
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"; // Import Form components
// import { useAuth } from '@/components/contexts/AuthContext'; // Conceptual, will be used later

// Define Zod schema for login form
const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }).nonempty({ message: "Email is required" }),
  password: z.string().nonempty({ message: "Password is required" }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  // const { login } = useAuth(); // Conceptual, will be used later
  const navigate = useNavigate();
  const { showToastError } = useToast(); // Use the custom hook

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

  // Placeholder submit function
  const onSubmit = async (data: LoginFormValues) => {
    console.log("Form submitted with data:", data);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      // Placeholder for actual login logic:
      // await login(data); 
      // toast.success('Logged in successfully!'); // For success, if needed
      // navigate('/dashboard');

      // Simulate an error for now
      throw new Error("Invalid credentials or server error");
    } catch (error: any) {
      showToastError(error.message || 'Login failed. Please check your credentials.');
      console.error("Login error", error);
    }
  };

  return (
    <Card className="w-full sm:w-96 mx-auto mt-24">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Login</CardTitle>
        <CardDescription>Enter your credentials to access your account.</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="you@example.com" {...field} />
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
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Your password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Login
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex flex-col items-center space-y-2">
        <p className="text-sm text-muted-foreground">
          Don't have an account?{' '}
          <Link to="/auth/register" className="font-medium text-primary hover:underline">
            Register
          </Link>
        </p>
        {/* Optional: Forgot password link
        <p className="text-sm text-muted-foreground">
          <Link to="/auth/forgot-password" className="font-medium text-primary hover:underline">
            Forgot Password?
          </Link>
        </p>
        */}
      </CardFooter>
    </Card>
  );
}
