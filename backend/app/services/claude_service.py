import json
import anthropic
from app.config import settings

WASP_SYSTEM_PROMPT = """You are an expert Wasp framework developer. Wasp is a DSL for building full-stack web applications with React and Node.js.

When generating a Wasp application, you must output valid JSON with these exact keys:
- main_wasp: The main.wasp file content
- schema_prisma: The schema.prisma file content  
- src_files: An object where keys are file paths (relative to src/) and values are file contents

Key Wasp concepts:
1. main.wasp defines: app config, routes, pages, queries, actions, auth
2. schema.prisma defines database models using Prisma syntax
3. src/ contains React components and server operations

Example main.wasp structure:
```
app MyApp {
  wasp: { version: "^0.20.0" },
  title: "My App",
  auth: {
    userEntity: User,
    methods: { usernameAndPassword: {} },
    onAuthFailedRedirectTo: "/login"
  }
}

route RootRoute { path: "/", to: MainPage }
page MainPage {
  authRequired: true,
  component: import { MainPage } from "@src/pages/MainPage"
}

query getTasks {
  fn: import { getTasks } from "@src/operations",
  entities: [Task]
}

action createTask {
  fn: import { createTask } from "@src/operations",
  entities: [Task]
}
```

Example schema.prisma:
```
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id    Int    @id @default(autoincrement())
  tasks Task[]
}

model Task {
  id          Int     @id @default(autoincrement())
  description String
  isDone      Boolean @default(false)
  userId      Int
  user        User    @relation(fields: [userId], references: [id])
}
```

Example src/operations.ts:
```typescript
import { type GetTasks, type CreateTask } from "wasp/server/operations";
import { type Task } from "wasp/entities";

export const getTasks: GetTasks<void, Task[]> = async (_args, context) => {
  if (!context.user) throw new Error("Not authenticated");
  return context.entities.Task.findMany({
    where: { userId: context.user.id }
  });
};

export const createTask: CreateTask<{ description: string }, Task> = async (args, context) => {
  if (!context.user) throw new Error("Not authenticated");
  return context.entities.Task.create({
    data: { description: args.description, userId: context.user.id }
  });
};
```

Example src/pages/MainPage.tsx:
```tsx
import { useQuery, getTasks } from "wasp/client/operations";
import { type User } from "wasp/entities";

export function MainPage({ user }: { user: User }) {
  const { data: tasks, isLoading } = useQuery(getTasks);
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>Welcome {user.id}</h1>
      <ul>
        {tasks?.map(task => <li key={task.id}>{task.description}</li>)}
      </ul>
    </div>
  );
}
```

Always include LoginPage and SignupPage when auth is enabled:

src/pages/auth.tsx:
```tsx
import { LoginForm, SignupForm } from "wasp/client/auth";

export function LoginPage() {
  return <LoginForm />;
}

export function SignupPage() {
  return <SignupForm />;
}
```

And routes in main.wasp:
```
route LoginRoute { path: "/login", to: LoginPage }
page LoginPage { component: import { LoginPage } from "@src/pages/auth" }

route SignupRoute { path: "/signup", to: SignupPage }
page SignupPage { component: import { SignupPage } from "@src/pages/auth" }
```

IMPORTANT: Output ONLY valid JSON, no markdown, no explanation."""


async def generate_wasp_app(name: str, description: str) -> dict:
    """Generate Wasp application code using Claude."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    user_prompt = f"""Create a Wasp application with the following requirements:

App Name: {name}
Description: {description}

Generate a complete, working Wasp application. Include authentication if the app involves user-specific data.
Output only valid JSON with main_wasp, schema_prisma, and src_files keys."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        system=WASP_SYSTEM_PROMPT
    )
    
    response_text = message.content[0].text
    
    # Parse JSON response
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(response_text[start:end])
        else:
            raise ValueError("Failed to parse Claude response as JSON")
    
    return result

