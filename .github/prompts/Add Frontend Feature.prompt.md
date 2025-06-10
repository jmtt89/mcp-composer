# Add Frontend Feature

Your goal is to add a new feature to the MCP Composer web interface.

Ask for the feature requirements if not provided:
- What functionality should be added
- Which UI components are needed
- API endpoints required
- User interaction flow

Requirements for frontend features:
- Modify the single-page application in [src/ui/index.html](src/ui/index.html)
- Use vanilla JavaScript (no external frameworks)
- Follow the existing CSS styling patterns
- Use the `/api/v1` prefix for API calls
- Implement proper error handling and user notifications
- Add loading states for async operations

Existing patterns to follow:
- **API calls**: Use the `apiCall()` helper function for all HTTP requests
- **UI updates**: Use DOM manipulation with proper element selection
- **Notifications**: Use `showNotification()` for user feedback
- **Loading states**: Add/remove `button-loading` class for buttons
- **Styling**: Follow the existing CSS class patterns and responsive design

Components available:
- Gateway cards with server kit details
- Server and tool toggle buttons
- Copy and delete functionality
- Modal dialogs for confirmations
- Status badges and button groups

Ensure the feature:
1. Integrates seamlessly with existing UI patterns
2. Provides proper user feedback for all actions
3. Handles errors gracefully with meaningful messages
4. Maintains responsive design principles
5. Uses semantic HTML and accessible markup
6. Follows the established JavaScript coding style
