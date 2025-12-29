import { definePlugin, routerHook } from "@decky/api";
import { staticClasses } from "@decky/ui";
import { FaSpotify } from "react-icons/fa";
import { STRINGS, ROUTES } from "./constants";
import { MainContent, SettingsContainer } from "./containers";

export default definePlugin(() => {
  console.log("Spotify Connect Speaker plugin initializing");

  // Register settings route
  routerHook.addRoute(ROUTES.SETTINGS, SettingsContainer, {
    exact: true
  });

  return {
    name: STRINGS.PLUGIN_NAME,
    titleView: (
      <div className={staticClasses.Title}>
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FaSpotify />
          {STRINGS.PLUGIN_TITLE}
        </span>
      </div>
    ),
    content: <MainContent />,
    icon: <FaSpotify />,
    onDismount() {
      console.log("Spotify Connect Speaker plugin unloading");
      routerHook.removeRoute(ROUTES.SETTINGS);
    }
  };
});
