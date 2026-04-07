export function mapProjectsById(projects) {
  return Object.fromEntries(projects.map((project) => [project.id, project]));
}

export function mapProjectsByKey(projects) {
  return Object.fromEntries(projects.map((project) => [project.key, project]));
}
