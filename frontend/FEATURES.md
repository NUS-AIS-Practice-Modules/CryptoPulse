# Frontend Feature List

## Rules

- Work on one feature at a time
- A feature is complete only after verification passes
- Prioritize the main chat flow first

## Features

### FE-001: Project Initialization (priority: 1)

**Description**: Initialize the React + TypeScript + Tailwind + Vite project.

**Verification**

- [ ] `npm install` succeeds
- [ ] `npm run dev` starts successfully
- [ ] `npm run build` succeeds
- [ ] Tailwind CSS is active

### FE-002: Chat Page UI (priority: 2)

**Description**: Build the main chat page.

**Verification**

- [ ] Input box accepts text
- [ ] Send button submits successfully
- [ ] User messages appear on the right
- [ ] AI messages appear on the left
- [ ] Message list supports scrolling
- [ ] Page layout renders correctly

### FE-003: Chat API Integration (priority: 3)

**Description**: Connect `POST /api/chat`.

**Verification**

- [ ] Clicking send calls the API
- [ ] Returned `reply` displays correctly
- [ ] Loading animation works
- [ ] `conversation_id` supports multi-turn chat
- [ ] API failures show an error message

### FE-004: File Upload Component (priority: 4)

**Description**: Build the file-upload UI component.

**Verification**

- [ ] File selection works
- [ ] File name is displayed
- [ ] PDF/TXT files are supported
- [ ] Upload-area UI renders correctly

### FE-005: Dashboard Page (priority: 5)

**Description**: Build the data-visualization page.

**Verification**

- [ ] Page is accessible
- [ ] Line chart shows trend data
- [ ] Pie chart shows sentiment distribution
- [ ] Data comes from the API
- [ ] Filter can switch the time range

### FE-006: Health Checks and Error Handling (priority: 6)

**Description**: Handle system status and failure feedback.

**Verification**

- [ ] `GET /api/health` can be called
- [ ] Backend failures are surfaced to the user
- [ ] Loading state behaves correctly
- [ ] Network errors show useful messages
