# Frontend Architecture Examples

> **Status:** Reference Examples
> **Companion to:** `frontend-standard.md` and `frontend-style.md`
> **Scope:** Routes, pages, components, typed API clients, hooks, mutations, forms, and shadcn/ui.

## Purpose

This file provides small examples for Vite React TypeScript code using shadcn/ui, Tailwind, typed hooks, and route-first design.

Use it after reading the standard and style guide. Adapt examples to the actual Helu module; do not copy them mechanically when an existing local pattern is more specific.

Adapt paths to the repository's current structure.

## Query Key Example

```ts
export type ProjectFilters = {
  status?: "active" | "archived"
  search?: string
  page: number
}

export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (filters: ProjectFilters) => [...projectKeys.lists(), filters] as const,
  detail: (id: string) => [...projectKeys.all, "detail", id] as const,
}
```

## Domain Type Example

```ts
export type ProjectSummary = {
  id: string
  name: string
  description: string
  status: "active" | "archived"
  ownerId: string
  createdAt: string
}

export type ProjectDetail = ProjectSummary & {
  tasks: ProjectTask[]
}

export type ProjectTask = {
  id: string
  title: string
  completed: boolean
}
```

## API Envelope Example

```ts
export type ApiEnvelope<T> = {
  data: T
}

export type ApiListEnvelope<T> = {
  data: T[]
  meta: {
    page: number
    perPage: number
    total: number
  }
}

export type ApiValidationError = {
  message: string
  errors?: Record<string, string[]>
}
```

## API Client Example

```ts
import { http } from "@/lib/http"
import type { ApiEnvelope, ApiListEnvelope } from "@/types/api"
import type { ProjectDetail, ProjectFilters, ProjectSummary } from "../model/project-types"

export async function getProjects(filters: ProjectFilters): Promise<ApiListEnvelope<ProjectSummary>> {
  return http.get("/projects", {
    params: filters,
  })
}

export async function getProject(id: string): Promise<ApiEnvelope<ProjectDetail>> {
  return http.get(`/projects/${id}`)
}

export type SaveProjectPayload = {
  project: {
    name: string
    description: string
  }
}

export async function createProject(payload: SaveProjectPayload): Promise<ApiEnvelope<ProjectDetail>> {
  return http.post("/projects", payload)
}
```

## Query Hook Example

```ts
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { getProject, getProjects } from "../api/projects-api"
import { projectKeys, type ProjectFilters } from "../model/project-keys"

const emptyProjectsResponse = {
  data: [],
  meta: {
    page: 1,
    perPage: 10,
    total: 0,
  },
}

export function useProjectsQuery(filters: ProjectFilters) {
  return useQuery({
    queryKey: projectKeys.list(filters),
    queryFn: () => getProjects(filters),
    placeholderData: keepPreviousData,
  })
}

export function useProjectQuery(id: string | undefined) {
  return useQuery({
    queryKey: id ? projectKeys.detail(id) : projectKeys.detail("missing"),
    queryFn: () => getProject(id as string),
    enabled: Boolean(id),
  })
}
```

## Mutation Hook Example

```ts
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { createProject, type SaveProjectPayload } from "../api/projects-api"
import { projectKeys } from "../model/project-keys"

export function useCreateProjectMutation() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (payload: SaveProjectPayload) => createProject(payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
      navigate(`/projects/${response.data.id}`)
    },
  })
}
```

## Optimistic Mutation Example

```ts
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { favoriteProject } from "../api/projects-api"
import { projectKeys, type ProjectFilters } from "../model/project-keys"
import type { ApiEnvelope, ApiListEnvelope } from "@/types/api"
import type { ProjectDetail, ProjectSummary } from "../model/project-types"

type FavoriteProjectVariables = {
  id: string
  filters: ProjectFilters
  favorited: boolean
}

type FavoriteProjectContext = {
  previousDetail?: ApiEnvelope<ProjectDetail>
  previousList?: ApiListEnvelope<ProjectSummary>
}

export function useFavoriteProjectMutation() {
  const queryClient = useQueryClient()

  return useMutation<ApiEnvelope<ProjectDetail>, Error, FavoriteProjectVariables, FavoriteProjectContext>({
    mutationFn: ({ id, favorited }) => favoriteProject(id, favorited),
    onMutate: async ({ id, filters, favorited }) => {
      await queryClient.cancelQueries({ queryKey: projectKeys.detail(id) })
      await queryClient.cancelQueries({ queryKey: projectKeys.list(filters) })

      const previousDetail = queryClient.getQueryData<ApiEnvelope<ProjectDetail>>(projectKeys.detail(id))
      const previousList = queryClient.getQueryData<ApiListEnvelope<ProjectSummary>>(projectKeys.list(filters))

      queryClient.setQueryData<ApiEnvelope<ProjectDetail>>(projectKeys.detail(id), (current) => {
        if (!current) return current

        return {
          ...current,
          data: {
            ...current.data,
            favorited,
          },
        }
      })

      queryClient.setQueryData<ApiListEnvelope<ProjectSummary>>(projectKeys.list(filters), (current) => {
        if (!current) return current

        return {
          ...current,
          data: current.data.map((project) =>
            project.id === id
              ? { ...project, favorited }
              : project,
          ),
        }
      })

      return { previousDetail, previousList }
    },
    onError: (_error, variables, context) => {
      if (context?.previousDetail) {
        queryClient.setQueryData(projectKeys.detail(variables.id), context.previousDetail)
      }

      if (context?.previousList) {
        queryClient.setQueryData(projectKeys.list(variables.filters), context.previousList)
      }
    },
    onSettled: (_data, _error, variables) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(variables.id) })
      queryClient.invalidateQueries({ queryKey: projectKeys.list(variables.filters) })
    },
  })
}
```

## shadcn + Tailwind Component Example

```tsx
import { Link } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import type { ProjectSummary } from "../model/project-types"

type ProjectCardProps = {
  project: ProjectSummary
  isOwner: boolean
  onArchive: (id: string) => void
}

export function ProjectCard({ project, isOwner, onArchive }: ProjectCardProps) {
  return (
    <Card>
      <CardHeader className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <CardTitle className="line-clamp-2">
            <Link to={`/projects/${project.id}`} className="hover:underline">
              {project.name}
            </Link>
          </CardTitle>

          <Badge variant={project.status === "active" ? "default" : "secondary"}>
            {project.status === "active" ? "Ativo" : "Arquivado"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <p className="line-clamp-3 text-sm text-muted-foreground">
          {project.description}
        </p>
      </CardContent>

      {isOwner ? (
        <CardFooter className="justify-end gap-2">
          <Button variant="outline" asChild>
            <Link to={`/projects/${project.id}/edit`}>Editar</Link>
          </Button>

          <Button variant="destructive" onClick={() => onArchive(project.id)}>
            Arquivar
          </Button>
        </CardFooter>
      ) : null}
    </Card>
  )
}
```

## Page Example

```tsx
import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ProjectCard } from "../components/project-card"
import { ProjectFiltersPanel } from "../components/project-filters-panel"
import { useProjectsQuery } from "../hooks/use-projects-query"
import type { ProjectFilters } from "../model/project-keys"

const initialFilters: ProjectFilters = {
  page: 1,
}

export function ProjectsPage() {
  const [filters, setFilters] = useState<ProjectFilters>(initialFilters)
  const projectsQuery = useProjectsQuery(filters)

  if (projectsQuery.isLoading) {
    return <ProjectsSkeleton />
  }

  if (projectsQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Erro ao carregar projetos</AlertTitle>
        <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
      </Alert>
    )
  }

  const projects = projectsQuery.data?.data ?? []

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Projetos</h1>
          <p className="text-muted-foreground">Acompanhe seus projetos ativos e arquivados.</p>
        </div>

        <Button>Novo projeto</Button>
      </header>

      <ProjectFiltersPanel filters={filters} onChange={setFilters} />

      {projects.length === 0 ? (
        <EmptyProjectsState />
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              isOwner={false}
              onArchive={() => undefined}
            />
          ))}
        </section>
      )}
    </main>
  )
}

function ProjectsSkeleton() {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-4 px-4 py-8 md:grid-cols-2">
      <Skeleton className="h-40 rounded-xl" />
      <Skeleton className="h-40 rounded-xl" />
    </div>
  )
}

function EmptyProjectsState() {
  return (
    <div className="rounded-lg border border-dashed p-8 text-center">
      <h2 className="text-lg font-medium">Nenhum projeto encontrado</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Ajuste os filtros ou crie um novo projeto.
      </p>
    </div>
  )
}
```

## Form Values Example

```ts
export type ProjectFormValues = {
  name: string
  description: string
}

export const emptyProjectFormValues: ProjectFormValues = {
  name: "",
  description: "",
}
```

## Form Component Example

```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import type { ProjectFormValues } from "../model/project-form-values"

type ProjectFormProps = {
  values: ProjectFormValues
  errors: Partial<Record<keyof ProjectFormValues, string>>
  isSubmitting: boolean
  onChange: (values: ProjectFormValues) => void
  onSubmit: () => void
}

export function ProjectForm({
  values,
  errors,
  isSubmitting,
  onChange,
  onSubmit,
}: ProjectFormProps) {
  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <fieldset className="space-y-4" disabled={isSubmitting}>
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="project-name">
            Nome
          </label>
          <Input
            id="project-name"
            value={values.name}
            onChange={(event) => onChange({ ...values, name: event.target.value })}
          />
          {errors.name ? <p className="text-sm text-destructive">{errors.name}</p> : null}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="project-description">
            Descrição
          </label>
          <Textarea
            id="project-description"
            value={values.description}
            onChange={(event) => onChange({ ...values, description: event.target.value })}
          />
          {errors.description ? (
            <p className="text-sm text-destructive">{errors.description}</p>
          ) : null}
        </div>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : "Salvar"}
        </Button>
      </fieldset>
    </form>
  )
}
```

## Guest Gated Action Example

```tsx
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/features/auth/hooks/use-auth"

type FavoriteButtonProps = {
  favorited: boolean
  onToggle: () => void
}

export function FavoriteButton({ favorited, onToggle }: FavoriteButtonProps) {
  const navigate = useNavigate()
  const { isAuth } = useAuth()

  return (
    <Button
      variant={favorited ? "default" : "outline"}
      onClick={() => {
        if (!isAuth) {
          navigate("/login")
          return
        }

        onToggle()
      }}
    >
      {favorited ? "Favoritado" : "Favoritar"}
    </Button>
  )
}
```

## Mock API Example

```ts
import type { ApiListEnvelope } from "@/types/api"
import type { ProjectFilters, ProjectSummary } from "../model/project-types"

const storageKey = "helu:mock:projects"

function loadProjects(): ProjectSummary[] {
  const raw = localStorage.getItem(storageKey)

  if (!raw) {
    return seedProjects()
  }

  return JSON.parse(raw) as ProjectSummary[]
}

function saveProjects(projects: ProjectSummary[]) {
  localStorage.setItem(storageKey, JSON.stringify(projects))
}

export async function mockGetProjects(filters: ProjectFilters): Promise<ApiListEnvelope<ProjectSummary>> {
  const projects = loadProjects()
  const filtered = projects.filter((project) => {
    if (filters.status && project.status !== filters.status) {
      return false
    }

    if (filters.search && !project.name.toLowerCase().includes(filters.search.toLowerCase())) {
      return false
    }

    return true
  })

  return {
    data: filtered,
    meta: {
      page: filters.page,
      perPage: 10,
      total: filtered.length,
    },
  }
}

function seedProjects(): ProjectSummary[] {
  const projects: ProjectSummary[] = [
    {
      id: "project-1",
      name: "Projeto inicial",
      description: "Projeto usado para desenvolvimento local.",
      status: "active",
      ownerId: "user-1",
      createdAt: new Date().toISOString(),
    },
  ]

  saveProjects(projects)

  return projects
}
```

## Bad Examples

Do not do this:

```tsx
export function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([])

  useEffect(() => {
    fetch("/api/projects")
      .then((res) => res.json())
      .then(setProjects)
  }, [])

  return <div style={{ padding: 20 }}>{projects.map((p) => <div>{p.name}</div>)}</div>
}
```

Problems:

- Uses `any`.
- Fetches directly in page.
- Uses inline style.
- Uses raw divs instead of existing UI primitives.
- No loading state.
- No error state.
- No empty state.
- No typed API envelope.
- No query key/cache behavior.