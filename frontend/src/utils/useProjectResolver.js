import { useEffect, useState } from "react";

import { api, parseApiError } from "../services/api";

export function useProjectResolver(projectId, projectKey) {
  const [project, setProject] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProject() {
      if (!projectId && !projectKey) {
        return;
      }
      try {
        let response;
        if (projectId) {
          response = await api.getProject(projectId);
        } else {
          response = await api.getProjectByKey(projectKey);
        }
        setProject(response.data);
        setError("");
      } catch (err) {
        setError(parseApiError(err));
      }
    }
    loadProject();
  }, [projectId, projectKey]);

  return { project, projectError: error };
}
