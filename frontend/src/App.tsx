import { Outlet, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import Feed from "./pages/Feed";
import Likes from "./pages/Likes";
import Chats from "./pages/Chats";
import Conversation from "./pages/Conversation";
import Profile from "./pages/Profile";
import ProfileEdit from "./pages/ProfileEdit";
import ProfilePhotos from "./pages/ProfilePhotos";
import ProfileSettings from "./pages/ProfileSettings";
import ProfileLanguage from "./pages/ProfileLanguage";
import ProfileSubscription from "./pages/ProfileSubscription";
import ProfileTelegram from "./pages/ProfileTelegram";
import ProfileVisits from "./pages/ProfileVisits";
import ProfileCompletion from "./pages/ProfileCompletion";
import ProfileVerify from "./pages/ProfileVerify";
import PublicProfile from "./pages/PublicProfile";
import SettingsDetail from "./pages/SettingsDetail";
import NotFound from "./pages/NotFound";
import Notifications from "./pages/Notifications";
import Guide from "./pages/Guide";
import DataExport from "./pages/DataExport";
import TermsOfService from "./pages/legal/TermsOfService";
import PrivacyPolicy from "./pages/legal/PrivacyPolicy";
import NotificationBootstrap from "./components/NotificationBootstrap";
import AdminLayout from "./admin/AdminLayout";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminModulePage from "./pages/admin/AdminModulePage";
import IncomingCallListener from "./components/IncomingCallListener";

function AuthenticatedServices() {
  return (<>
    <NotificationBootstrap />
    <Outlet />
  </>);
}

/**
 * Production-oriented beta shell. Auth, profile, feed, social and messaging
 * flows progressively use the real API while preserving the validated UI.
 */
export default function App() {
  return (
    <>
      <IncomingCallListener />
      <Routes>
      <Route path="/" element={<SignIn />} />
      <Route path="/signin" element={<SignIn />} />
      <Route path="/signup" element={<SignUp />} />
      {/* Public: must be reachable before login (linked from the signup
          consent checkbox) and after login (linked from Settings). */}
      <Route path="/legal/terms" element={<TermsOfService />} />
      <Route path="/legal/privacy" element={<PrivacyPolicy />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AuthenticatedServices />}>
        {/* Conversation has its own full-screen layout (no bottom nav) */}
        <Route path="/chats/:id" element={<Conversation />} />
        <Route path="/profile/view/:chatId" element={<PublicProfile />} />

        <Route element={<AppLayout />}>
          <Route path="/feed" element={<Feed />} />
          <Route path="/likes" element={<Likes />} />
          <Route path="/chats" element={<Chats />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/profile/edit" element={<ProfileEdit />} />
          <Route path="/profile/photos" element={<ProfilePhotos />} />
          <Route path="/profile/settings" element={<ProfileSettings />} />
          <Route path="/profile/language" element={<ProfileLanguage />} />
          <Route path="/profile/subscription" element={<ProfileSubscription />} />
          <Route path="/profile/telegram" element={<ProfileTelegram />} />
          <Route path="/profile/visits" element={<ProfileVisits />} />
          <Route path="/profile/completion" element={<ProfileCompletion />} />
          <Route path="/profile/verify" element={<ProfileVerify />} />
          <Route path="/settings/:slug" element={<SettingsDetail />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/guide" element={<Guide />} />
          <Route path="/privacy/export" element={<DataExport />} />
        </Route>
        </Route>
      </Route>

      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<AdminModulePage section="users" />} />
        <Route path="profiles" element={<AdminModulePage section="profiles" />} />
        <Route path="vip" element={<AdminModulePage section="vip" />} />
        <Route path="likes" element={<AdminModulePage section="likes" />} />
        <Route path="messages" element={<AdminModulePage section="messages" />} />
        <Route path="reports" element={<AdminModulePage section="reports" />} />
        <Route path="subscriptions" element={<AdminModulePage section="subscriptions" />} />
        <Route path="payments" element={<AdminModulePage section="payments" />} />
        <Route path="notifications" element={<AdminModulePage section="notifications" />} />
        <Route path="analytics" element={<AdminModulePage section="analytics" />} />
        <Route path="settings" element={<AdminModulePage section="settings" />} />
      </Route>

      <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
