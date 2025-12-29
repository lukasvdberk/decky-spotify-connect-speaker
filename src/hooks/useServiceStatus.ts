import { useState, useEffect, useCallback } from "react";
import { toaster } from "@decky/api";
import type { ServiceStatus } from "../types";
import { STRINGS } from "../constants";
import * as api from "../api";

interface UseServiceStatusReturn {
  status: ServiceStatus | null;
  isLoading: boolean;
  isToggling: boolean;
  isRestarting: boolean;
  refreshStatus: () => Promise<void>;
  toggleService: () => Promise<void>;
  restartService: () => Promise<void>;
}

export const useServiceStatus = (): UseServiceStatusReturn => {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isToggling, setIsToggling] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);

  const refreshStatus = useCallback(async () => {
    try {
      const newStatus = await api.getStatus();
      setStatus(newStatus);
    } catch (error) {
      console.error("Failed to get status:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_FAILED_STATUS
      });
    }
  }, []);

  const toggleService = useCallback(async () => {
    if (!status) return;
    setIsToggling(true);
    try {
      const success = status.running
        ? await api.stopSpotifyd()
        : await api.startSpotifyd();

      if (success) {
        toaster.toast({
          title: STRINGS.TOAST_SUCCESS,
          body: status.running ? STRINGS.TOAST_STOPPED : STRINGS.TOAST_STARTED
        });
        await refreshStatus();
      } else {
        toaster.toast({
          title: STRINGS.TOAST_ERROR,
          body: status.running ? STRINGS.TOAST_FAILED_STOP : STRINGS.TOAST_FAILED_START
        });
      }
    } catch (error) {
      console.error("Toggle service error:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_OPERATION_FAILED
      });
    } finally {
      setIsToggling(false);
    }
  }, [status, refreshStatus]);

  const restartService = useCallback(async () => {
    setIsRestarting(true);
    try {
      const success = await api.restartSpotifyd();
      if (success) {
        toaster.toast({
          title: STRINGS.TOAST_SUCCESS,
          body: STRINGS.TOAST_RESTARTED
        });
        await refreshStatus();
      } else {
        toaster.toast({
          title: STRINGS.TOAST_ERROR,
          body: STRINGS.TOAST_FAILED_RESTART
        });
      }
    } catch (error) {
      console.error("Restart error:", error);
      toaster.toast({
        title: STRINGS.TOAST_ERROR,
        body: STRINGS.TOAST_FAILED_RESTART
      });
    } finally {
      setIsRestarting(false);
    }
  }, [refreshStatus]);

  useEffect(() => {
    const loadInitialStatus = async () => {
      setIsLoading(true);
      await refreshStatus();
      setIsLoading(false);
    };
    loadInitialStatus();
  }, [refreshStatus]);

  return {
    status,
    isLoading,
    isToggling,
    isRestarting,
    refreshStatus,
    toggleService,
    restartService
  };
};
