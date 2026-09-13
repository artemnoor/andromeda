import { getCurrentProfile, getCurrentRecommendations, type CurrentProfileResponse, type CurrentRecommendationsResponse } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { components } from "../../api/generated";

type Results = components["schemas"]["ProftestResultsResponse"];

export async function loadPersistedResults(): Promise<Results | null> {
  try {
    const profile = await getCurrentProfile();
    const recommendations = await getCurrentRecommendations();
    return toResults(profile, recommendations);
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 404) {
      console.warn("[proftest] current_profile_empty");
      return null;
    }
    throw error;
  }
}

function toResults(profile: CurrentProfileResponse, recommendations: CurrentRecommendationsResponse): Results {
  return { profile: profile.profile, recommendations: recommendations.recommendations };
}
