from collections import defaultdict
from typing import List, Dict
from dora.service.deployments.models.models import Deployment
from dora.service.incidents.incident_filter import apply_incident_filter
from dora.store.models.incidents.filter import IncidentFilter
from dora.store.models.settings import EntityType, SettingType
from dora.utils.time import Interval

from dora.store.models.incidents import Incident
from dora.service.settings.configuration_settings import (
    SettingsService,
    get_settings_service,
)
from dora.store.repos.incidents import IncidentsRepoService


class IncidentService:
    def __init__(
        self,
        incidents_repo_service: IncidentsRepoService,
        settings_service: SettingsService,
    ):
        self._incidents_repo_service = incidents_repo_service
        self._settings_service = settings_service

    def get_resolved_team_incidents(
        self, team_id: str, interval: Interval
    ) -> List[Incident]:
        incident_filter: IncidentFilter = apply_incident_filter(
            entity_type=EntityType.TEAM,
            entity_id=team_id,
            setting_types=[
                SettingType.INCIDENT_SETTING,
                SettingType.INCIDENT_TYPES_SETTING,
            ],
        )
        return self._incidents_repo_service.get_resolved_team_incidents(
            team_id, interval, incident_filter
        )

    def get_team_incidents(self, team_id: str, interval: Interval) -> List[Incident]:
        incident_filter: IncidentFilter = apply_incident_filter(
            entity_type=EntityType.TEAM,
            entity_id=team_id,
            setting_types=[
                SettingType.INCIDENT_SETTING,
                SettingType.INCIDENT_TYPES_SETTING,
            ],
        )
        return self._incidents_repo_service.get_team_incidents(
            team_id, interval, incident_filter
        )

    def get_deployment_incidents_map(
        self, deployments: List[Deployment], incidents: List[Incident]
    ):
        deployments = sorted(deployments, key=lambda x: x.conducted_at)
        incidents = sorted(incidents, key=lambda x: x.creation_date)
        incidents_pointer = 0

        deployment_incidents_map: Dict[Deployment, List[Incident]] = defaultdict(list)

        for current_deployment, next_deployment in zip(
            deployments, deployments[1:] + [None]
        ):
            current_deployment_incidents = []

            if incidents_pointer >= len(incidents):
                deployment_incidents_map[
                    current_deployment
                ] = current_deployment_incidents
                continue

            while incidents_pointer < len(incidents):
                incident = incidents[incidents_pointer]

                if incident.creation_date >= current_deployment.conducted_at and (
                    next_deployment is None
                    or incident.creation_date < next_deployment.conducted_at
                ):
                    current_deployment_incidents.append(incident)
                    incidents_pointer += 1
                elif incident.creation_date < current_deployment.conducted_at:
                    incidents_pointer += 1
                else:
                    break

            deployment_incidents_map[current_deployment] = current_deployment_incidents

        return deployment_incidents_map


def get_incident_service():
    return IncidentService(IncidentsRepoService(), get_settings_service())