"""Editing the bots' prompts, with their shipped defaults to fall back on."""

from dataclasses import dataclass

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.core.files import read_text, write_text
from pidash.prompts.validation import check_placeholders
from pidash.services.catalog import Prompt, Service, get_service, services_with


@dataclass(frozen=True)
class EditablePrompt:
    service: Service
    prompt: Prompt
    text: str
    default: str
    modified: bool
    missing: bool

    @property
    def field_name(self) -> str:
        return f"{self.service.id}__{self.prompt.id}"


def _paths(service: Service, prompt_id: str):
    base = service.prompts_dir
    return base / f"{prompt_id}.txt", base / f"{prompt_id}.default.txt"


def _load(service: Service, prompt: Prompt) -> EditablePrompt:
    path, default_path = _paths(service, prompt.id)
    default = read_text(default_path)
    # On a fresh clone only the default exists; show that, it is what the bot will use.
    text = read_text(path, default)
    return EditablePrompt(
        service=service,
        prompt=prompt,
        text=text,
        default=default,
        modified=bool(default) and text != default,
        missing=not path.is_file(),
    )


class PromptsView(TemplateView):
    template_name = "prompts/page.html"

    def get_context_data(self, **kwargs):
        available = services_with("prompts")
        chosen = self.request.GET.get("service") or (available[0].id if available else "")
        service = get_service(chosen)
        prompts = [_load(service, prompt) for prompt in service.prompts] if service else []
        return super().get_context_data(
            page_title="Prompts",
            page_subtitle="What each bot asks the model to do.",
            services=available,
            service=service,
            prompts=prompts,
            **kwargs,
        )


def _prompt_or_404(service_id: str, prompt_id: str):
    service = get_service(service_id)
    prompt = service.prompt(prompt_id) if service else None
    if service is None or prompt is None:
        raise Http404("No such prompt")
    return service, prompt


@require_POST
def save(request, service_id: str, prompt_id: str):
    service, prompt = _prompt_or_404(service_id, prompt_id)
    text = request.POST.get("text", "").replace("\r\n", "\n")
    back = f"{request.POST.get('next') or '/prompts/'}"

    if not text.strip():
        messages.error(request, "A prompt can't be empty.")
        return redirect(back)

    problem = check_placeholders(text, prompt.vars)
    if problem:
        messages.error(request, problem)
        return redirect(back)

    path, _default = _paths(service, prompt.id)
    if not path.parent.is_dir():
        messages.error(request, f"{service.name} has no prompts folder.")
        return redirect(back)

    try:
        write_text(path, text)
    except PermissionError:
        messages.error(request, f"Not allowed to write {path}.")
        return redirect(back)

    when = "next run" if service.kind == "scheduled" else "next check"
    messages.success(request, f"{prompt.label} saved — applies on the {when}.")
    return redirect(back)


@require_POST
def reset(request, service_id: str, prompt_id: str):
    service, prompt = _prompt_or_404(service_id, prompt_id)
    path, default_path = _paths(service, prompt.id)
    back = f"{request.POST.get('next') or '/prompts/'}"

    default = read_text(default_path)
    if not default:
        messages.error(request, "There's no shipped default for this prompt.")
        return redirect(back)
    try:
        write_text(path, default)
    except PermissionError:
        messages.error(request, f"Not allowed to write {path}.")
        return redirect(back)
    messages.success(request, f"{prompt.label} reset to the original.")
    return redirect(back)
