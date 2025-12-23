# ntfy.sh Notification Configuration Example

This example shows how to configure ntfy.sh push notifications in klondike.

## Basic Configuration

Add this to your `.klondike/config.yaml`:

```yaml
# Push notifications via ntfy.sh (https://ntfy.sh)
# Sends notifications for session events, feature completions, etc.
ntfy:
  # Required: The ntfy topic/channel to publish to
  channel: my-klondike-topic
  
  # Optional: Custom ntfy server (defaults to https://ntfy.sh)
  server: https://ntfy.sh
  
  # Optional: Access token for authentication (recommended for private topics)
  # Get a token at https://ntfy.sh/account
  token: tk_your_token_here
  
  # Optional: Configure which events trigger notifications
  events:
    session_start: true      # Notify when session starts
    session_end: true        # Notify when session ends
    feature_verified: true   # Notify when feature is verified
    feature_blocked: true    # Notify when feature is blocked
    errors: true             # Notify on errors (not yet implemented)
```

## Getting Started

### 1. Choose a Topic Name

Pick a unique topic name for your notifications. This is essentially your "channel":

- Good: `myproject-alerts`, `jane-klondike`, `team-backend`
- Avoid: Common words like `test`, `notifications` (others might use them)

### 2. Subscribe on Your Device

#### Mobile App (Android/iOS)

1. Download ntfy from:
   - [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
   - [F-Droid](https://f-droid.org/en/packages/io.heckel.ntfy/)
   - [App Store](https://apps.apple.com/us/app/ntfy/id1625396347)

2. Open the app and tap "Subscribe to topic"
3. Enter your topic name (e.g., `myproject-alerts`)

#### Web Browser

Visit https://ntfy.sh/your-topic-name

### 3. Configure klondike

Update your `.klondike/config.yaml` with the ntfy configuration shown above.

### 4. Test It

Start a new session to test:

```bash
klondike session start --focus "Testing notifications"
```

You should receive a notification on your device! 🎉

## Authentication (Optional but Recommended)

For private topics, you can use access tokens:

1. Create an account at https://ntfy.sh/account
2. Create an access token
3. Add it to your config:

```yaml
ntfy:
  channel: my-private-topic
  token: tk_your_token_here
```

## Notification Types

### Session Start
- **Priority**: Normal (3)
- **Title**: 🚀 Session #X Started
- **Tags**: `rocket`

### Session End
- **Priority**: Normal (3)
- **Title**: ✅ Session #X Complete (N features completed)
- **Tags**: `checkered_flag`, `tada` (if features completed)

### Feature Verified
- **Priority**: Normal (3)
- **Title**: ✅ F00X Verified
- **Tags**: `white_check_mark`, `tada`

### Feature Blocked
- **Priority**: High (4)
- **Title**: ⛔ F00X Blocked
- **Tags**: `no_entry`, `warning`

## Troubleshooting

### Not Receiving Notifications?

1. **Check topic name matches** between config and your subscription
2. **Verify connectivity**: Visit https://ntfy.sh/your-topic in a browser
3. **Test with curl**:
   ```bash
   curl -d "Test message" https://ntfy.sh/your-topic
   ```
4. **Check mobile app settings**: Ensure notifications are enabled for the ntfy app

### Rate Limiting

ntfy.sh has rate limits:
- **Initial burst**: 60 requests per IP
- **Refill rate**: 1 request per 5 seconds

If you hit the limit, klondike will log a warning but won't crash.

### Private Topics

Without authentication, anyone can subscribe to your topic. To keep it private:
1. Create a ntfy.sh account
2. Use access tokens in your config
3. Or self-host ntfy (see https://docs.ntfy.sh/install/)

## Advanced: Self-Hosting

You can run your own ntfy server:

```yaml
ntfy:
  channel: my-topic
  server: https://ntfy.example.com
  token: tk_your_token_here
```

See https://docs.ntfy.sh/install/ for setup instructions.

## Example Complete Config

```yaml
# Klondike CLI Configuration

default_category: core
default_priority: 2
verified_by: coding-agent
progress_output_path: agent-progress.md
auto_regenerate_progress: true
klondike_version: 1.0.9
configured_agents: [copilot]

# Push notifications
ntfy:
  channel: myproject-alerts
  server: https://ntfy.sh
  events:
    session_start: true
    session_end: true
    feature_verified: true
    feature_blocked: true
    errors: true
```
