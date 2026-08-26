"""Brand↔creator campaign services."""
from analytics.services import record_event
from core.exceptions import AppError
from campaigns.models import Application, Campaign


class CampaignService:
    @staticmethod
    def create(brand_user, *, title: str, brief: str, budget_inr: int,
               deliverables=None, min_audience: int = 0, payout_inr=None) -> Campaign:
        brand = getattr(brand_user, "brand_profile", None)
        if not brand:
            raise AppError("Only brand accounts can create campaigns.", code="brand_required")
        if not title or budget_inr <= 0:
            raise AppError("Title and a positive budget are required.",
                           code="validation_error")
        campaign = Campaign.objects.create(
            brand_user=brand_user,
            brand=brand,
            title=title[:140],
            brief=brief[:3000],
            deliverables=[str(d)[:120] for d in (deliverables or [])][:8],
            budget_inr=int(budget_inr),
            payout_inr=int(payout_inr) if payout_inr else None,
            min_audience=max(0, int(min_audience or 0)),
            status=Campaign.Status.OPEN,
        )
        record_event(user=brand_user, name="campaign_created",
                     properties={"campaign_id": str(campaign.id)})
        return campaign

    @staticmethod
    def apply(creator_profile, campaign: Campaign, pitch: str) -> Application:
        if campaign.status != Campaign.Status.OPEN:
            raise AppError("This campaign isn't accepting applications.",
                           code="campaign_closed")
        if creator_profile.user_id == campaign.brand_user_id:
            raise AppError("That's your own campaign.", code="invalid_application")
        if campaign.min_audience and creator_profile.audience_size < campaign.min_audience:
            raise AppError(
                f"This campaign needs an audience of at least {campaign.min_audience}.",
                code="audience_too_small",
            )
        application, created = Application.objects.get_or_create(
            campaign=campaign, creator=creator_profile,
            defaults={"pitch": pitch[:1500]},
        )
        if created:
            record_event(user=creator_profile.user, name="campaign_applied",
                         properties={"campaign_id": str(campaign.id)})
        return application

    @staticmethod
    def review(campaign_owner, application: Application, *, accept: bool) -> Application:
        if application.campaign.brand_user_id != campaign_owner.id:
            raise AppError("Not your campaign.", code="permission_denied")
        application.status = (Application.Status.ACCEPTED if accept
                              else Application.Status.REJECTED)
        application.save(update_fields=["status", "updated_at"])
        from notifications.services import notify

        notify(application.creator.user, type="system",
               title=f"Campaign {application.status.lower()}",
               body=application.campaign.title[:100],
               data={"campaign_id": str(application.campaign_id)})
        return application
