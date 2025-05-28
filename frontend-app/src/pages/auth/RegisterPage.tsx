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
import { Label } from '@/components/ui/label'; // Note: FormLabel from ui/form is typically used with FormField
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
// import { useAuth } from '@/components/contexts/AuthContext'; // Conceptual, will be used later

// Define Zod schema for registration form
const registerSchema = z.object({
  username: z.string().nonempty({ message: "Username is required" }).min(3, { message: "Username must be at least 3 characters" }),
  email: z.string().email({ message: "Invalid email address" }).nonempty({ message: "Email is required" }),
  password: z.string().nonempty({ message: "Password is required" }).min(6, { message: "Password must be at least 6 characters" }),
  confirmPassword: z.string().nonempty({ message: "Please confirm your password" }),
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"], // Set error on confirmPassword field
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  // const { register } = useAuth(); // Conceptual, will be used later
  const navigate = useNavigate();
  const { showToastSuccess, showToastError } = useToast(); // Use the custom hook

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

  // Placeholder submit function
  const onSubmit = async (data: RegisterFormValues) => {
    console.log("Register form submitted with data:", data);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      // Placeholder for actual registration logic:
      // await register({ name: data.username, email: data.email, password: data.password }); 
      
      // Simulate a success scenario for now
      showToastSuccess('Registration successful! Please check your email to verify.');
      navigate('/login'); // Or to a verify-email page

      // To simulate an error:
      // throw new Error("Registration failed. Please try again.");
    } catch (error: any) {
      showToastError(error.message || 'Registration failed. Please try again.');
      console.error("Registration error", error);
    }
  };

  return (
    <Card className="w-full sm:w-96 mx-auto mt-24">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Create an Account</CardTitle>
        <CardDescription>Enter your details to register.</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Username</FormLabel>
                  <FormControl>
                    <Input placeholder="Your username" {...field} />
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
                    <Input type="password" placeholder="Choose a password" {...field} />
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
                  <FormLabel>Confirm Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Confirm your password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Create Account
            </Button>
          </form>
        </Form>
      </CardContent>
      <CardFooter className="flex flex-col items-center space-y-2">
        <p className="text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Login
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
