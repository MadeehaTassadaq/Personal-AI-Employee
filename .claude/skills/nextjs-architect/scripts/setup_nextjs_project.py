#!/usr/bin/env python3
"""
Next.js 16 Project Setup Script
This script creates a new Next.js 16 project with best practices and recommended configuration.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_nextjs_project(project_name):
    """Create a new Next.js project with TypeScript and recommended options"""
    print(f"Creating Next.js 16 project: {project_name}")

    # Create the project using create-next-app
    cmd = [
        "npx", "create-next-app@latest",
        project_name,
        "--typescript",
        "--tailwind",
        "--eslint",
        "--app",
        "--src-dir",
        "--import-alias",
        "@/*"
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Created Next.js project: {project_name}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create project: {e}")
        sys.exit(1)

def update_package_json(project_path):
    """Update package.json with recommended scripts and dependencies"""
    package_json_path = Path(project_path) / "package.json"

    with open(package_json_path, 'r') as f:
        package_json = json.load(f)

    # Add recommended scripts
    package_json['scripts'].update({
        "dev": "next dev",
        "build": "next build",
        "start": "next start",
        "lint": "next lint",
        "type-check": "tsc --noEmit",
        "format": "prettier --write ."
    })

    # Add recommended dependencies
    dev_dependencies = {
        "@types/node": "^20",
        "@types/react": "^18",
        "@types/react-dom": "^18",
        "autoprefixer": "^10.4.19",
        "postcss": "^8.4.38",
        "tailwindcss": "^3.4.3",
        "eslint-config-next": "14.2.3",
        "prettier": "^3.2.5"
    }

    if 'devDependencies' not in package_json:
        package_json['devDependencies'] = {}
    package_json['devDependencies'].update(dev_dependencies)

    # Write updated package.json
    with open(package_json_path, 'w') as f:
        json.dump(package_json, f, indent=2)

    print("✓ Updated package.json with recommended configuration")

def create_tsconfig(project_path):
    """Create recommended tsconfig.json"""
    tsconfig_path = Path(project_path) / "tsconfig.json"

    tsconfig = {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "es6"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [
                {
                    "name": "next"
                }
            ],
            "baseUrl": ".",
            "paths": {
                "@/*": ["./src/*"]
            }
        },
        "include": [
            "next-env.d.ts",
            "**/*.ts",
            "**/*.tsx",
            ".next/types/**/*.ts"
        ],
        "exclude": ["node_modules"]
    }

    with open(tsconfig_path, 'w') as f:
        json.dump(tsconfig, f, indent=2)

    print("✓ Created recommended tsconfig.json")

def create_prettier_config(project_path):
    """Create Prettier configuration"""
    prettier_config = {
        "semi": true,
        "trailingComma": "es5",
        "singleQuote": True,
        "printWidth": 80,
        "tabWidth": 2,
        "useTabs": False,
        "bracketSpacing": True,
        "arrowParens": "avoid"
    }

    prettier_path = Path(project_path) / ".prettierrc"
    with open(prettier_path, 'w') as f:
        json.dump(prettier_config, f, indent=2)

    print("✓ Created Prettier configuration")

def create_directory_structure(project_path):
    """Create recommended directory structure"""
    src_path = Path(project_path) / "src"

    directories = [
        src_path / "app",
        src_path / "components",
        src_path / "lib",
        src_path / "hooks",
        src_path / "types",
        src_path / "styles",
        src_path / "utils"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print("✓ Created recommended directory structure")

def create_example_components(project_path):
    """Create example components to demonstrate best practices"""
    components_path = Path(project_path) / "src" / "components"

    # Create a reusable button component
    button_component = '''\
"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
'''

    button_path = components_path / "ui" / "button.tsx"
    button_path.parent.mkdir(parents=True, exist_ok=True)

    with open(button_path, 'w') as f:
        f.write(button_component)

    print("✓ Created example button component")

def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_nextjs.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1]

    print(f"Setting up Next.js 16 project: {project_name}")

    create_nextjs_project(project_name)
    create_directory_structure(project_name)
    update_package_json(project_name)
    create_tsconfig(project_name)
    create_prettier_config(project_name)
    create_example_components(project_name)

    print(f"\n✓ Next.js 16 project setup complete!")
    print(f"✓ Navigate to {project_name} and run 'npm install' to install dependencies")
    print(f"✓ Then run 'npm run dev' to start the development server")

if __name__ == "__main__":
    main()