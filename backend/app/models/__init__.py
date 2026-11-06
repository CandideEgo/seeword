# Import all models in dependency order so SQLAlchemy can resolve relationships
from app.models.admin_setting import AdminSetting
from app.models.behavior import BehaviorEvent
from app.models.catalog import CatalogItem
from app.models.channel import Channel
from app.models.content_publication import ContentPublicationOperation, TeachingContentDraft
from app.models.data_export import DataExportTask
from app.models.engagement import VideoLike
from app.models.exam_corpus import ExamSentence, ExamSentenceWord, ExamWordFreq
from app.models.exam_test import ExamAnswer, ExamPaper, ExamQuestion, ExamSession
from app.models.favorite import UserFavorite, UserNote
from app.models.feedback import Feedback
from app.models.home_content import HomeContentDraft, HomeContentRevision, HomePageConfig
from app.models.jinshuju_payment import JinshujuPayment
from app.models.learning import LearningRecord, Vocabulary
from app.models.learning_plan import LearningEvent, UserLearningProfile
from app.models.listening import ListeningSession
from app.models.media_cleanup import MediaCleanupTask
from app.models.milestone import MasterySnapshot, UserMilestone
from app.models.notification import Notification
from app.models.order import Order
from app.models.pipeline_dispatch import PipelineDispatch
from app.models.preferences import UserPreferences
from app.models.question_exposure import UserExposureMappingState, UserQuestionExposure
from app.models.study_session import StudySession, StudySessionItem
from app.models.subtitle import Subtitle
from app.models.subtitle_resegment_snapshot import SubtitleResegmentSnapshot
from app.models.subtitle_revision import SubtitleRevision
from app.models.teaching import (
    ExamAnalysisRevision,
    ExamEvidence,
    LearningEventOutbox,
    TeachingAttempt,
    TeachingFeedback,
    TeachingItem,
    TeachingOperation,
    TeachingSession,
    UserQuestionDisclosure,
)
from app.models.user import User
from app.models.user_content import ChannelSubscription, SentenceFavorite
from app.models.user_video_unlock import UserVideoUnlock
from app.models.v2_runtime import (
    AgentRun,
    AgentRunEvent,
    AgentStep,
    ExternalConnection,
    ExternalCredential,
    GatewayLifecycleIntent,
    TeachingAccessGrant,
    TeachingMessage,
    TeachingMessageBlock,
)
from app.models.video import Video
from app.models.video_quality_report import VideoQualityReport
from app.models.video_score import VideoScore
from app.models.video_standard import VideoStandard
from app.models.vocab_set import VocabSet, VocabSetWord
from app.models.word_note import WordAINote
