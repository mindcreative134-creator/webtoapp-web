// wta_webview.m — WebToApp macOS standalone-window helper.
//
// Opens WTA_URL in a real WKWebView window while running INSIDE our own
// .app bundle, so CFBundleName (menu bar), the icns icon and the bundle's
// ATS exceptions all apply — things an osascript/JXA process can never get
// (issue #30). Shipped as a prebuilt universal binary in every macos.zip;
// rebuild it on any Mac with ./build.sh.
//
// Configuration arrives through the environment set by the bundle launcher:
//   WTA_URL   target to load (required)
//   WTA_NAME  window / menu-bar title
//   WTA_ICON  absolute path to the bundle's .icns
//   WTA_DEBUG when set, logs the resolved bundle path to stderr
// Exit codes: 0 after a normal window session; 3 when there is no usable
// target, so the shell launcher can fall back to older launch paths.

#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

static NSString *Env(NSString *key) {
    return [[[NSProcessInfo processInfo] environment] objectForKey:key];
}

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property(strong) NSWindow *window;
@property(strong) WKWebView *webView;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    (void)notification;
    NSString *urlString = Env(@"WTA_URL") ?: @"";
    NSString *name = Env(@"WTA_NAME") ?: @"App";
    NSString *iconPath = Env(@"WTA_ICON");

    NSURL *url = [NSURL URLWithString:urlString];
    NSString *scheme = url.scheme.lowercaseString;
    if (!(url.host && ([scheme isEqualToString:@"https"] || [scheme isEqualToString:@"http"]))) {
        fprintf(stderr, "wta_webview: no usable WTA_URL target\n");
        exit(3);
    }

    CGFloat width = 1280, height = 800;
    NSWindowStyleMask mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                             NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable;
    self.window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0, 0, width, height)
                                              styleMask:mask
                                                backing:NSBackingStoreBuffered
                                                  defer:NO];
    self.window.title = name;
    self.window.contentMinSize = NSMakeSize(480, 320);
    [self.window center];

    self.webView = [[WKWebView alloc] initWithFrame:NSMakeRect(0, 0, width, height)];
    self.window.contentView = self.webView;

    if (iconPath) {
        NSImage *icon = [[NSImage alloc] initWithContentsOfFile:iconPath];
        if (icon) [NSApp setApplicationIconImage:icon];
    }
    [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
    if (@available(macOS 14.0, *)) {
        [NSApp activate];
    } else {
        [NSApp activateIgnoringOtherApps:YES];
    }

    // Plain-http loads need the bundle Info.plist ATS exception; without it
    // WKWebView refuses them and the user sees a blank page.
    [self.webView loadRequest:[NSURLRequest requestWithURL:url]];
    [self.window makeKeyAndOrderFront:nil];

    if (getenv("WTA_DEBUG")) {
        fprintf(stderr, "wta_webview: bundle=%s url=%s\n",
                NSBundle.mainBundle.bundlePath.UTF8String ?: "(none)",
                urlString.UTF8String);
    }
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    (void)sender;
    return YES;
}

@end

int main(int argc, const char **argv) {
    (void)argc;
    (void)argv;
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        AppDelegate *delegate = [AppDelegate new];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
