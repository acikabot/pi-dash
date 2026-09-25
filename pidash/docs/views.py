"""Reading the project's documentation inside the dashboard."""

from django.http import FileResponse, Http404
from django.views.generic import TemplateView

from pidash.docs import documents as docs


class DocIndexView(TemplateView):
    template_name = "docs/index.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            page_title="Documentation",
            page_subtitle="Rendered from the Markdown in this project, so it is never stale.",
            documents=docs.documents_for(self.request.user).values(),
            **kwargs,
        )


class DocPageView(TemplateView):
    template_name = "docs/page.html"

    def get_context_data(self, **kwargs):
        document = docs.get_document(self.kwargs["slug"], self.request.user)
        if document is None:
            raise Http404("No such document")
        return super().get_context_data(
            page=docs.render(document),
            documents=docs.documents_for(self.request.user).values(),
            **kwargs,
        )


def image(request, name: str):
    """A picture from docs/images/, for the documentation pages."""
    path = docs.image_path(name)
    if path is None:
        raise Http404("No such image")
    response = FileResponse(path.open("rb"), content_type=docs.IMAGE_TYPES[path.suffix.lower()])
    # An SVG is a document in its own right: make sure nothing inside it can ever run.
    response["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'"
    response["Cache-Control"] = "private, max-age=3600"
    return response
