describe('Login Flow', () => {
  beforeEach(() => {
    // Visit the login page before each test
    cy.visit('/login');
  });

  it('should allow a user to log in successfully and redirect to dashboard', () => {
    // Use placeholder credentials - these would need to work against the auth system (mocked or real)
    const email = 'testuser@example.com';
    const password = 'password123';

    // Assuming standard input field selectors; data-testid would be more robust
    // Attempt to find by placeholder first, then by name attribute
    cy.get('input[placeholder="name@example.com"]').should('be.visible').type(email);
    cy.get('input[placeholder="••••••••"]').should('be.visible').type(password);

    // Assuming the submit button is of type submit
    cy.get('button[type="submit"]').should('be.visible').contains('Login').click();

    // Assert redirection to the dashboard
    cy.url().should('include', '/dashboard');

    // Assert that dashboard specific to an individual user is shown
    // Assuming 'testuser@example.com' is an individual user.
    // These assertions require data-cy attributes on the dashboard cards.
    cy.get('[data-cy="dashboard-card-active-profiles"]').should('be.visible').and('contain.text', 'Active Profiles');
    cy.get('[data-cy="dashboard-card-my-profile-performance"]').should('be.visible').and('contain.text', 'My Profile Performance');

    // A more generic check for successful login can remain (e.g., logout button in nav)
    // This selector will likely need adjustment based on the actual Navbar component.
    // cy.get('nav').should('be.visible').and('contain.text', 'Logout'); // Example
    
    // Optional: Check localStorage for a token (if applicable)
    // cy.window().its('localStorage.token').should('be.a', 'string');
  });

  it('should display an error message for invalid credentials', () => {
    const email = 'testuser@example.com';
    const invalidPassword = 'wrongpassword';

    cy.get('input[placeholder="name@example.com"]').type(email);
    cy.get('input[placeholder="••••••••"]').type(invalidPassword);
    cy.get('button[type="submit"]').contains('Login').click();

    // Assert that the user remains on the login page (or error is shown)
    cy.url().should('include', '/login'); // Or check that it doesn't navigate away significantly

    // Assert that an error message is displayed
    // The exact text and selector will depend on how errors are shown in LoginPage.tsx
    // Common patterns: a div with a specific class, or role="alert"
    cy.get('[role="alert"]') // A common way to show form errors
      .should('be.visible')
      .and('contain.text', 'Invalid credentials'); // Adjust text based on actual error message
                                                  // This could also be "Invalid email or password"
  });

  it('should display client-side validation messages for empty fields', () => {
    // Attempt to submit with empty email
    cy.get('button[type="submit"]').contains('Login').click();
    
    // Check for validation message near email input
    // Assuming error messages appear near the input, possibly associated by aria-describedby
    // Or, if using shadcn/ui, FormMessage component might be used.
    // Let's assume the error message for email contains "Email is required" or similar.
    // This selector is a guess and highly dependent on the actual HTML structure.
    cy.get('input[placeholder="name@example.com"]')
      .siblings('[role="alert"], [data-form-message="error"]') // Common patterns for error messages
      .should('be.visible')
      .and('contain.text', 'Email is required'); // Adjust based on actual validation message

    // Fill email, attempt to submit with empty password
    cy.get('input[placeholder="name@example.com"]').type('test@example.com');
    cy.get('button[type="submit"]').contains('Login').click();

    // Check for validation message near password input
    cy.get('input[placeholder="••••••••"]')
      .siblings('[role="alert"], [data-form-message="error"]')
      .should('be.visible')
      .and('contain.text', 'Password is required'); // Adjust based on actual validation message
  });

  it('should navigate to register page when "Sign up" link is clicked', () => {
    cy.contains("Don't have an account? Sign up").should('be.visible').click();
    cy.url().should('include', '/register');
  });
  
  it('should navigate to forgot password page when "Forgot password?" link is clicked', () => {
    cy.contains("Forgot password?").should('be.visible').click();
    cy.url().should('include', '/forgot-password');
  });

});
