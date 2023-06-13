__version__ = "0.0.1b2"

from typing import Any, Dict, List, Optional, TypeVar

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from fastapi_swagger2.utils import get_swagger2

AppType = TypeVar("AppType", bound="FastAPI")


class FastAPISwagger2:
    def __init__(
        self,
        app: AppType,
        swagger2_url: Optional[str] = "/swagger2.json",
        swagger2_tags: Optional[List[Dict[str, Any]]] = None,
        swagger2_docs_url: Optional[str] = "/swagger2/docs",
        swagger2_redoc_url: Optional[str] = "/swagger2/redoc",
        swagger2_ui_oauth2_redirect_url: Optional[
            str
        ] = "/swagger2/docs/oauth2-redirect",
        swagger2_ui_init_oauth: Optional[Dict[str, Any]] = None,
        swagger2_ui_parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.app = app
        self.swagger2_url = swagger2_url
        self.swagger2_tags = swagger2_tags
        self.swagger2_docs_url = swagger2_docs_url
        self.swagger2_redoc_url = swagger2_redoc_url
        self.swagger2_ui_oauth2_redirect_url = swagger2_ui_oauth2_redirect_url
        self.swagger2_ui_init_oauth = swagger2_ui_init_oauth
        self.swagger2_ui_parameters = swagger2_ui_parameters

        self.swagger2_version = "2.0"
        self.swagger2_schema: Optional[Dict[str, Any]] = None
        if self.swagger2_url:
            assert (
                self.app.title
            ), "A title must be provided for Swagger, e.g.: 'My API'"
            assert (
                self.app.version
            ), "A version must be provided for Swagger, e.g.: '2.1.0'"

        self.setup()

    def setup(self) -> None:
        if self.swagger2_url:
            urls = (server_data.get("url") for server_data in self.app.servers)
            server_urls = {url for url in urls if url}

            async def swagger2(req: Request) -> JSONResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                if root_path not in server_urls:
                    if root_path and self.app.root_path_in_servers:
                        self.app.servers.insert(0, {"url": root_path})
                        server_urls.add(root_path)
                return JSONResponse(self.swagger2())

            self.app.add_route(self.swagger2_url, swagger2, include_in_schema=False)

        if self.swagger2_url and self.swagger2_docs_url:

            async def swagger_ui_html(req: Request) -> HTMLResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                swagger2_url = root_path + self.swagger2_url
                oauth2_redirect_url = self.swagger2_ui_oauth2_redirect_url
                if oauth2_redirect_url:
                    oauth2_redirect_url = root_path + oauth2_redirect_url
                return get_swagger_ui_html(
                    openapi_url=swagger2_url,
                    title=self.app.title + " - Swagger UI",
                    oauth2_redirect_url=oauth2_redirect_url,
                    init_oauth=self.swagger2_ui_init_oauth,
                    swagger_ui_parameters=self.swagger2_ui_parameters,
                )

            self.app.add_route(
                self.swagger2_docs_url, swagger_ui_html, include_in_schema=False
            )

            if self.swagger2_ui_oauth2_redirect_url:

                async def swagger_ui_redirect(req: Request) -> HTMLResponse:
                    return get_swagger_ui_oauth2_redirect_html()

                self.app.add_route(
                    self.swagger2_ui_oauth2_redirect_url,
                    swagger_ui_redirect,
                    include_in_schema=False,
                )
        if self.swagger2_url and self.swagger2_redoc_url:

            async def redoc_html(req: Request) -> HTMLResponse:
                root_path = req.scope.get("root_path", "").rstrip("/")
                swagger2_url = root_path + self.swagger2_url
                return get_redoc_html(
                    openapi_url=swagger2_url, title=self.app.title + " - ReDoc"
                )

            self.app.add_route(
                self.swagger2_redoc_url, redoc_html, include_in_schema=False
            )

    def swagger2(self) -> Dict[str, Any]:
        if not self.swagger2_schema:
            self.swagger2_schema = get_swagger2(
                title=self.app.title,
                version=self.app.version,
                swagger2_version=self.swagger2_version,
                description=self.app.description,
                terms_of_service=self.app.terms_of_service,
                contact=self.app.contact,
                license_info=self.app.license_info,
                routes=self.app.routes,
                tags=self.swagger2_tags,
            )

        return self.swagger2_schema
