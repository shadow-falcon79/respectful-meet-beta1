import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import SubPageHeader from "../components/SubPageHeader";
import { getMySettings, updateMySettings, type UserSettings } from "../api/settings";
import { useLanguage } from "../store/LanguageContext";

const copy: Record<string, Record<string,string>> = {
 EN:{account:"Account",privacy:"Privacy",notifications:"Notifications",security:"Security",help:"Help",terms:"Terms","privacy-policy":"Privacy Policy",language:"Language",appearance:"Appearance",discovery:"Discovery"},
 FR:{account:"Compte",privacy:"Confidentialité",notifications:"Notifications",security:"Sécurité",help:"Aide",terms:"Conditions","privacy-policy":"Politique de confidentialité",language:"Langue",appearance:"Apparence",discovery:"Découverte"},
 ES:{account:"Cuenta",privacy:"Privacidad",notifications:"Notificaciones",security:"Seguridad",help:"Ayuda",terms:"Términos","privacy-policy":"Política de privacidad",language:"Idioma",appearance:"Apariencia",discovery:"Descubrimiento"},
 PT:{account:"Conta",privacy:"Privacidade",notifications:"Notificações",security:"Segurança",help:"Ajuda",terms:"Termos","privacy-policy":"Política de privacidade",language:"Idioma",appearance:"Aparência",discovery:"Descoberta"},
 AR:{account:"الحساب",privacy:"الخصوصية",notifications:"الإشعارات",security:"الأمان",help:"المساعدة",terms:"الشروط","privacy-policy":"سياسة الخصوصية",language:"اللغة",appearance:"المظهر",discovery:"الاكتشاف"},
 DE:{account:"Konto",privacy:"Datenschutz",notifications:"Benachrichtigungen",security:"Sicherheit",help:"Hilfe",terms:"Bedingungen","privacy-policy":"Datenschutzerklärung",language:"Sprache",appearance:"Darstellung",discovery:"Entdecken"},
 IT:{account:"Account",privacy:"Privacy",notifications:"Notifiche",security:"Sicurezza",help:"Aiuto",terms:"Termini","privacy-policy":"Informativa sulla privacy",language:"Lingua",appearance:"Aspetto",discovery:"Scoperta"},
 RU:{account:"Аккаунт",privacy:"Конфиденциальность",notifications:"Уведомления",security:"Безопасность",help:"Помощь",terms:"Условия","privacy-policy":"Политика конфиденциальности",language:"Язык",appearance:"Внешний вид",discovery:"Знакомства"},
 ZH:{account:"账户",privacy:"隐私",notifications:"通知",security:"安全",help:"帮助",terms:"条款","privacy-policy":"隐私政策",language:"语言",appearance:"外观",discovery:"发现"},
 JA:{account:"アカウント",privacy:"プライバシー",notifications:"通知",security:"セキュリティ",help:"ヘルプ",terms:"利用規約","privacy-policy":"プライバシーポリシー",language:"言語",appearance:"表示",discovery:"検索設定"},
 TR:{account:"Hesap",privacy:"Gizlilik",notifications:"Bildirimler",security:"Güvenlik",help:"Yardım",terms:"Koşullar","privacy-policy":"Gizlilik Politikası",language:"Dil",appearance:"Görünüm",discovery:"Keşfet"},
};

export default function SettingsDetail(){
 const {slug}=useParams<{slug:string}>(); const {language,setLanguage}=useLanguage(); const t=copy[language]??copy.EN;
 const [settings,setSettings]=useState<UserSettings|null>(null); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
 useEffect(()=>{getMySettings().then(setSettings).catch(e=>setError(e instanceof Error?e.message:"Unable to load settings."));},[]);
 async function patch(p:Partial<UserSettings>){if(!settings)return;setBusy(true);setError("");try{setSettings(await updateMySettings(p));}catch(e){setError(e instanceof Error?e.message:"Unable to save settings.");}finally{setBusy(false);}}
 const title=t[slug??""]??(slug??"Settings");
 const Toggle=({label,keyName}:{label:string;keyName:keyof UserSettings})=><label className="settings-row"><span>{label}</span><input type="checkbox" checked={Boolean(settings?.[keyName])} disabled={busy} onChange={e=>void patch({[keyName]:e.target.checked} as Partial<UserSettings>)}/></label>;
 return <section className="page"><SubPageHeader title={title} backTo="/profile/settings"/>{error&&<p role="alert">{error}</p>}
  {slug==="notifications"&&settings&&<div className="stack" style={{marginTop:16}}><Toggle label="Push notifications" keyName="push_notifications"/><Toggle label="Email notifications" keyName="email_notifications"/><Toggle label="Product and marketing updates" keyName="marketing_notifications"/></div>}
  {slug==="privacy"&&settings&&<div className="stack" style={{marginTop:16}}><Toggle label="Show me as online" keyName="show_online_status"/><Toggle label="Allow my profile in discovery" keyName="profile_discoverable"/><Toggle label="Show my age" keyName="show_age"/><Toggle label="Show my city" keyName="show_city"/></div>}
  {slug==="discovery"&&settings&&<div className="stack" style={{marginTop:16}}><label className="card" style={{padding:18}}>Minimum age<input className="input" type="number" min="18" max="100" value={settings.min_age} onChange={e=>setSettings({...settings,min_age:Number(e.target.value)})} onBlur={()=>void patch({min_age:settings.min_age})}/></label><label className="card" style={{padding:18}}>Maximum age<input className="input" type="number" min="18" max="100" value={settings.max_age} onChange={e=>setSettings({...settings,max_age:Number(e.target.value)})} onBlur={()=>void patch({max_age:settings.max_age})}/></label><label className="card" style={{padding:18}}>Discovery radius (km)<input className="input" type="number" min="1" max="5000" value={settings.discovery_radius_km} onChange={e=>setSettings({...settings,discovery_radius_km:Number(e.target.value)})} onBlur={()=>void patch({discovery_radius_km:settings.discovery_radius_km})}/></label></div>}
  {slug==="language"&&<div className="stack" style={{marginTop:16}}>{(["EN","FR","ES","PT","AR","DE","IT","RU","ZH","JA","TR"] as const).map(code=><button key={code} className="settings-row" onClick={()=>{setLanguage(code);void patch({language:code});}}><span>{code}</span><span>{language===code?"✓":"›"}</span></button>)}</div>}
  {["account","security","help"].includes(slug??"")&&<div className="stack" style={{marginTop:16}}><article className="card" style={{padding:18}}><p>{slug==="security"?"Use a secure email account, never share verification codes, and report suspicious activity.":slug==="help"?"Use the Guide & Help section for account, messaging, safety and Premium assistance.":"Your account and profile settings are managed securely by the Respectful Meet backend."}</p></article></div>}
 </section>;
}
