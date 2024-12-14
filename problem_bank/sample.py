progress = models.FloatField(help_text="Progress as a percentage.")
completed = models.BooleanField(
    default=False, help_text="Indicates if all topics are cleared."
)
question_set_category = models.ForeignKey(
    QuestionCategory,
    on_delete=models.CASCADE,
    related_name="user_question_sets",
    help_text="Category of the question set.",
)
examination_level = models.CharField(
    max_length=10, choices=EXAMINATION_LEVELS, help_text="Examination level."
)
academic_class = models.CharField(max_length=50, help_text="E.g., Form 1, Form 2.")
cleared_topics = models.PositiveIntegerField(
    default=0, help_text="Number of topics cleared by the user."
)


@property
def is_progress_complete(self):
    """Check if progress is 100%."""
    return self.progress == 100.0


def update_progress(self):
    """
    Updates the progress based on topics passed and total topics in the associated category.
    """
    total_topics = self.question_set_category.total_topics
    if total_topics > 0:
        self.progress = (self.cleared_topics / total_topics) * 100
    else:
        self.progress = 0
    self.completed = self.progress == 100.0
    self.save()
