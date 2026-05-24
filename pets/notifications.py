from .models import MissingPetNotification


def create_missing_pet_notification(report, event_type, title, message, sighting=None):
    return MissingPetNotification.objects.create(
        user=report.owner,
        missing_pet=report,
        sighting=sighting,
        event_type=event_type,
        title=title,
        message=message,
    )


def notify_missing_report_created(report):
    return create_missing_pet_notification(
        report=report,
        event_type="missing_reported",
        title=f"{report.pet_name} missing alert published",
        message=f"Your missing pet alert for {report.pet_name} is now visible to the community.",
    )


def notify_sighting_reported(report, sighting):
    return create_missing_pet_notification(
        report=report,
        sighting=sighting,
        event_type="sighting_reported",
        title=f"New sighting for {report.pet_name}",
        message=f"Someone reported seeing {report.pet_name} near {sighting.sighting_location}.",
    )


def notify_found_status_changed(report):
    if report.is_found:
        return create_missing_pet_notification(
            report=report,
            event_type="marked_found",
            title=f"{report.pet_name} marked as found",
            message=f"Your missing pet report for {report.pet_name} has been marked as found.",
        )

    return create_missing_pet_notification(
        report=report,
        event_type="reopened_missing",
        title=f"{report.pet_name} missing alert reopened",
        message=f"Your missing pet report for {report.pet_name} is active again.",
    )
