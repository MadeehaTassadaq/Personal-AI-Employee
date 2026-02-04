import { useState } from 'react';

interface ComposePanelProps {
  onSubmit: (platform: string, content: string, options?: PostOptions) => Promise<void>;
}

interface PostOptions {
  imageUrl?: string;
  link?: string;
  recipient?: string;
  subject?: string;
}

type Platform = 'facebook' | 'instagram' | 'twitter' | 'linkedin' | 'whatsapp' | 'email';

const PLATFORMS: { id: Platform; name: string; icon: string; maxLength?: number; requiresImage?: boolean; requiresRecipient?: boolean }[] = [
  { id: 'facebook', name: 'Facebook', icon: '[fb]', maxLength: 63206 },
  { id: 'instagram', name: 'Instagram', icon: '[ig]', maxLength: 2200, requiresImage: true },
  { id: 'twitter', name: 'Twitter/X', icon: '[tw]', maxLength: 280 },
  { id: 'linkedin', name: 'LinkedIn', icon: '[in]', maxLength: 3000 },
  { id: 'whatsapp', name: 'WhatsApp', icon: '[wa]', requiresRecipient: true },
  { id: 'email', name: 'Email', icon: '[em]', requiresRecipient: true },
];

export function ComposePanel({ onSubmit }: ComposePanelProps) {
  const [platform, setPlatform] = useState<Platform>('facebook');
  const [content, setContent] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [linkUrl, setLinkUrl] = useState('');
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const currentPlatform = PLATFORMS.find(p => p.id === platform)!;
  const charCount = content.length;
  const isOverLimit = currentPlatform.maxLength ? charCount > currentPlatform.maxLength : false;

  const handleSubmit = async () => {
    setError(null);
    setSuccess(null);

    // Validation
    if (!content.trim()) {
      setError('Please enter content for your post');
      return;
    }

    if (currentPlatform.requiresImage && !imageUrl.trim()) {
      setError('Instagram posts require an image URL');
      return;
    }

    if (currentPlatform.requiresRecipient && !recipient.trim()) {
      setError(`Please enter a recipient for ${currentPlatform.name}`);
      return;
    }

    if (platform === 'email' && !subject.trim()) {
      setError('Email requires a subject line');
      return;
    }

    if (isOverLimit) {
      setError(`Content exceeds ${currentPlatform.maxLength} character limit`);
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(platform, content, {
        imageUrl: imageUrl || undefined,
        link: linkUrl || undefined,
        recipient: recipient || undefined,
        subject: subject || undefined,
      });

      setSuccess(`${currentPlatform.name} post submitted for approval!`);
      setContent('');
      setImageUrl('');
      setLinkUrl('');
      setRecipient('');
      setSubject('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit post');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getPlaceholder = () => {
    switch (platform) {
      case 'twitter':
        return "What's happening? (max 280 characters)";
      case 'linkedin':
        return 'Share a professional update...';
      case 'instagram':
        return 'Write a caption for your image...';
      case 'whatsapp':
        return 'Type your message...';
      case 'email':
        return 'Compose your email...';
      default:
        return "What's on your mind?";
    }
  };

  return (
    <div className="panel compose-panel">
      <div className="panel-header">
        <h2>Compose</h2>
        <span className="badge">Post & Message</span>
      </div>

      {error && (
        <div className="compose-error">
          {error}
        </div>
      )}

      {success && (
        <div className="compose-success">
          {success}
        </div>
      )}

      <div className="compose-content">
        {/* Platform Selector */}
        <div className="platform-selector">
          {PLATFORMS.map(p => (
            <button
              key={p.id}
              className={`platform-btn ${platform === p.id ? 'active' : ''}`}
              onClick={() => setPlatform(p.id)}
              title={p.name}
            >
              <span className="platform-icon">{p.icon}</span>
              <span className="platform-label">{p.name}</span>
            </button>
          ))}
        </div>

        {/* Recipient field for WhatsApp/Email */}
        {currentPlatform.requiresRecipient && (
          <div className="compose-field">
            <label>{platform === 'email' ? 'To (email address)' : 'To (phone with country code)'}</label>
            <input
              type="text"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder={platform === 'email' ? 'recipient@example.com' : '+1234567890'}
              className="compose-input"
            />
          </div>
        )}

        {/* Subject for Email */}
        {platform === 'email' && (
          <div className="compose-field">
            <label>Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject line"
              className="compose-input"
            />
          </div>
        )}

        {/* Image URL for Instagram */}
        {currentPlatform.requiresImage && (
          <div className="compose-field">
            <label>Image URL (must be publicly accessible)</label>
            <input
              type="url"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/image.jpg"
              className="compose-input"
            />
          </div>
        )}

        {/* Optional Link URL for Facebook/LinkedIn */}
        {(platform === 'facebook' || platform === 'linkedin') && (
          <div className="compose-field">
            <label>Link URL (optional)</label>
            <input
              type="url"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="compose-input"
            />
          </div>
        )}

        {/* Main Content */}
        <div className="compose-field">
          <label>
            {platform === 'email' ? 'Message' : 'Content'}
            {currentPlatform.maxLength && (
              <span className={`char-count ${isOverLimit ? 'over-limit' : ''}`}>
                {charCount}/{currentPlatform.maxLength}
              </span>
            )}
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={getPlaceholder()}
            className="compose-textarea"
            rows={platform === 'twitter' ? 3 : 5}
          />
        </div>

        {/* Preview */}
        {content && (
          <div className="compose-preview">
            <h4>Preview</h4>
            <div className="preview-content">
              <div className="preview-platform">
                <span>{currentPlatform.icon}</span>
                <span>{currentPlatform.name}</span>
              </div>
              {recipient && (
                <div className="preview-recipient">
                  To: {recipient}
                </div>
              )}
              {subject && (
                <div className="preview-subject">
                  Subject: {subject}
                </div>
              )}
              {imageUrl && (
                <div className="preview-image">
                  <img src={imageUrl} alt="Preview" onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }} />
                </div>
              )}
              <div className="preview-text">{content}</div>
              {linkUrl && (
                <div className="preview-link">{linkUrl}</div>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="compose-actions">
          <button
            className="btn btn-primary compose-submit"
            onClick={handleSubmit}
            disabled={isSubmitting || isOverLimit || !content.trim()}
          >
            {isSubmitting ? 'Submitting...' : 'Submit for Approval'}
          </button>
          <span className="compose-hint">
            Posts are reviewed before being published
          </span>
        </div>
      </div>
    </div>
  );
}
