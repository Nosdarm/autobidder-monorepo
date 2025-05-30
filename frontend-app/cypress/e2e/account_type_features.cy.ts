// Placeholder credentials - replace with actual test user credentials
const individualUser = {
  email: 'individual@example.com', // Replace with actual individual user email
  password: 'password123',    // Replace with actual password
};

const agencyUser = {
  email: 'agency@example.com', // Replace with actual agency user email
  password: 'password123',   // Replace with actual password
};

describe('Account Type Specific Features', () => {
  context('Individual User', () => {
    beforeEach(() => {
      // Programmatic login or UI login for individual user
      // Assuming a custom command cy.login() or direct API call for session setup
      // For UI login:
      cy.visit('/login');
      cy.get('input[placeholder="name@example.com"]').type(individualUser.email);
      cy.get('input[placeholder="••••••••"]').type(individualUser.password);
      cy.get('button[type="submit"]').contains('Login').click();
      cy.url().should('include', '/dashboard'); // Ensure login is successful
    });

    it('should NOT see "Team Management" link in SideNav', () => {
      // Assuming SideNav is rendered and visible on dashboard or other main pages
      // data-cy attribute would be on the <li> or <a> tag for the nav item
      cy.get('[data-cy="sidenav-link-team"]').should('not.exist');
    });

    it('should see "Access Denied" when navigating to /team directly', () => {
      cy.visit('/team');
      // Check for the access denied message specific to TeamPage.tsx
      // This requires TeamPage.tsx to render a specific element for this state.
      cy.get('[data-cy="team-page-access-denied-message"]').should('be.visible')
        .and('contain.text', 'This page is only accessible to Agency accounts'); // Or the translated equivalent
    });

    it('should see "Create Profile" button text on ProfilesPage', () => {
      cy.visit('/profiles');
      cy.get('[data-cy="profiles-page-create-button"]')
        .should('be.visible')
        .and('contain.text', 'Create Profile'); // Or its translated equivalent
    });

    // Add a logout step if running multiple user types in sequence without cy.session or similar
    afterEach(() => {
      // Implement logout if necessary, e.g., clicking a logout button
      // cy.get('[data-cy="logout-button"]').click(); 
    });
  });

  context('Agency User', () => {
    beforeEach(() => {
      // Programmatic login or UI login for agency user
      cy.visit('/login');
      cy.get('input[placeholder="name@example.com"]').type(agencyUser.email);
      cy.get('input[placeholder="••••••••"]').type(agencyUser.password);
      cy.get('button[type="submit"]').contains('Login').click();
      cy.url().should('include', '/dashboard'); // Ensure login is successful
    });

    it('should SEE "Team Management" link in SideNav', () => {
      cy.get('[data-cy="sidenav-link-team"]').should('be.visible');
    });

    it('should navigate to Team Management page successfully', () => {
      cy.get('[data-cy="sidenav-link-team"]').click();
      cy.url().should('include', '/team');
      // Check for a title or unique element on the TeamPage
      cy.get('[data-cy="team-page-title"]').should('be.visible').and('contain.text', 'Team Management'); // Or translated
    });

    it('should see "Add New Profile" button text on ProfilesPage', () => {
      cy.visit('/profiles');
      cy.get('[data-cy="profiles-page-create-button"]')
        .should('be.visible')
        .and('contain.text', 'Add New Profile'); // Or its translated equivalent
    });

    // Add a logout step
    afterEach(() => {
      // Implement logout
      // cy.get('[data-cy="logout-button"]').click();
    });
  });
});
