import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Activity, TrendingUp, Bell, BellOff, AlertCircle, Target, Clock, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [matches, setMatches] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [lastAlertCount, setLastAlertCount] = useState(0);

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      toast.error('Seu navegador não suporta notificações');
      return false;
    }

    if (Notification.permission === 'granted') {
      setNotificationsEnabled(true);
      toast.success('Notificações ativadas');
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setNotificationsEnabled(true);
        toast.success('Notificações ativadas com sucesso!');
        return true;
      }
    }

    toast.error('Permissão de notificação negada');
    return false;
  };

  const sendNotification = (title, body, icon) => {
    if (notificationsEnabled && Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon: icon || '/favicon.ico',
        badge: '/favicon.ico',
        vibrate: [200, 100, 200]
      });
    }
  };

  const fetchMatches = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/matches/live`);
      setMatches(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching matches:', error);
      setLoading(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/alerts`);
      const newAlerts = response.data;
      
      // Check if there are new alerts
      if (newAlerts.length > lastAlertCount && lastAlertCount > 0) {
        const latestAlert = newAlerts[0];
        sendNotification(
          `🚨 Alerta de Virada: ${latestAlert.team_name}`,
          `${latestAlert.team_name} vs ${latestAlert.opponent} (${latestAlert.score}) - ${Math.round(latestAlert.probability)}% de chance de virada!`,
          latestAlert.team_logo
        );
        toast.success(`Nova oportunidade: ${latestAlert.team_name}!`, {
          description: `${Math.round(latestAlert.probability)}% de chance de virada`
        });
      }
      
      setAlerts(newAlerts);
      setLastAlertCount(newAlerts.length);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, [lastAlertCount, notificationsEnabled]);

  const checkForNewAlerts = useCallback(async () => {
    try {
      await axios.post(`${API}/matches/check-comebacks`);
      await fetchAlerts();
    } catch (error) {
      console.error('Error checking alerts:', error);
    }
  }, [fetchAlerts]);

  useEffect(() => {
    fetchMatches();
    fetchAlerts();

    // Poll every 10 seconds for match updates
    const matchInterval = setInterval(fetchMatches, 10000);
    
    // Check for new alerts every 15 seconds
    const alertInterval = setInterval(checkForNewAlerts, 15000);

    return () => {
      clearInterval(matchInterval);
      clearInterval(alertInterval);
    };
  }, [fetchMatches, fetchAlerts, checkForNewAlerts]);

  const getComebackColor = (probability) => {
    if (probability >= 75) return 'text-green-400';
    if (probability >= 60) return 'text-yellow-400';
    if (probability >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const getComebackLabel = (probability) => {
    if (probability >= 75) return 'Muito Alta';
    if (probability >= 60) return 'Alta';
    if (probability >= 40) return 'Média';
    return 'Baixa';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="shimmer h-12 w-48 mx-auto rounded-lg"></div>
          <p className="text-green-300">Carregando partidas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8" data-testid="dashboard">
      {/* Header */}
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold gradient-text mb-2" data-testid="dashboard-title">
              Comeback Scout
            </h1>
            <p className="text-base md:text-lg text-green-200/80">
              Monitor de viradas em tempo real
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={notificationsEnabled ? () => setNotificationsEnabled(false) : requestNotificationPermission}
              variant={notificationsEnabled ? "default" : "outline"}
              className={notificationsEnabled ? "bg-green-600 hover:bg-green-700" : "border-green-600 text-green-400 hover:bg-green-600/10"}
              data-testid="notification-toggle-btn"
            >
              {notificationsEnabled ? <Bell className="mr-2 h-4 w-4" /> : <BellOff className="mr-2 h-4 w-4" />}
              {notificationsEnabled ? 'Notificações Ativas' : 'Ativar Notificações'}
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="glass p-6 border-green-500/20" data-testid="live-matches-card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Activity className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-green-300/70">Jogos Ao Vivo</p>
                <p className="text-2xl font-bold text-green-100">{matches.length}</p>
              </div>
            </div>
          </Card>

          <Card className="glass p-6 border-green-500/20" data-testid="comeback-scenarios-card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-500/20 rounded-lg">
                <TrendingUp className="h-6 w-6 text-yellow-400" />
              </div>
              <div>
                <p className="text-sm text-green-300/70">Cenários de Virada</p>
                <p className="text-2xl font-bold text-green-100">
                  {matches.filter(m => m.is_comeback_scenario).length}
                </p>
              </div>
            </div>
          </Card>

          <Card className="glass p-6 border-green-500/20" data-testid="alerts-card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-red-500/20 rounded-lg">
                <AlertCircle className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <p className="text-sm text-green-300/70">Alertas Gerados</p>
                <p className="text-2xl font-bold text-green-100">{alerts.length}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Live Matches */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 bg-red-500 rounded-full pulse-animation"></div>
            <h2 className="text-2xl md:text-3xl font-semibold text-green-100">Partidas Ao Vivo</h2>
          </div>

          {matches.length === 0 ? (
            <Card className="glass p-12 text-center border-green-500/20">
              <Target className="h-12 w-12 text-green-400/50 mx-auto mb-4" />
              <p className="text-green-300/70">Nenhuma partida ao vivo no momento</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {matches.map((match) => (
                <Card
                  key={match.id}
                  className={`match-card glass border-2 p-6 space-y-4 ${
                    match.is_comeback_scenario ? 'border-yellow-500/50 shadow-lg shadow-yellow-500/20' : 'border-green-500/20'
                  }`}
                  data-testid={`match-card-${match.home_team.name}`}
                >
                  {/* Match Header */}
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="border-green-500 text-green-400">
                      <Clock className="mr-1 h-3 w-3" />
                      {match.minute}'
                    </Badge>
                    {match.is_comeback_scenario && (
                      <Badge className="bg-yellow-500/20 text-yellow-300 border border-yellow-500/50">
                        <Zap className="mr-1 h-3 w-3" />
                        Chance de Virada!
                      </Badge>
                    )}
                  </div>

                  {/* Teams and Score */}
                  <div className="space-y-4">
                    {/* Home Team */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <img src={match.home_team.logo} alt={match.home_team.name} className="h-10 w-10" />
                        <span className={`text-lg font-semibold ${
                          match.losing_team === match.home_team.name ? 'text-red-400' : 'text-green-100'
                        }`}>
                          {match.home_team.name}
                        </span>
                      </div>
                      <span className="text-3xl font-bold text-green-100">{match.home_team.score}</span>
                    </div>

                    <Separator className="bg-green-500/20" />

                    {/* Away Team */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <img src={match.away_team.logo} alt={match.away_team.name} className="h-10 w-10" />
                        <span className={`text-lg font-semibold ${
                          match.losing_team === match.away_team.name ? 'text-red-400' : 'text-green-100'
                        }`}>
                          {match.away_team.name}
                        </span>
                      </div>
                      <span className="text-3xl font-bold text-green-100">{match.away_team.score}</span>
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-green-500/20">
                    <div className="text-center">
                      <p className="text-xs text-green-300/70 mb-1">Posse</p>
                      <p className="text-sm font-semibold text-green-100">{match.home_team.possession}%</p>
                      <p className="text-sm font-semibold text-green-100">{match.away_team.possession}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-green-300/70 mb-1">Chutes</p>
                      <p className="text-sm font-semibold text-green-100">{match.home_team.shots}</p>
                      <p className="text-sm font-semibold text-green-100">{match.away_team.shots}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-green-300/70 mb-1">xG</p>
                      <p className="text-sm font-semibold text-green-100">{match.home_team.xg}</p>
                      <p className="text-sm font-semibold text-green-100">{match.away_team.xg}</p>
                    </div>
                  </div>

                  {/* Comeback Probability */}
                  {match.is_comeback_scenario && (
                    <div className="space-y-2 pt-4 border-t border-yellow-500/20">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-green-300/90">Probabilidade de Virada</span>
                        <span className={`text-lg font-bold ${getComebackColor(match.comeback_probability)}`}>
                          {Math.round(match.comeback_probability)}%
                        </span>
                      </div>
                      <Progress value={match.comeback_probability} className="h-2" data-testid={`comeback-progress-${match.home_team.name}`} />
                      <p className="text-xs text-green-300/70 text-center">
                        {getComebackLabel(match.comeback_probability)}
                      </p>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl md:text-3xl font-semibold text-green-100">Alertas Recentes</h2>
            <Card className="glass border-green-500/20 p-6" data-testid="recent-alerts">
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {alerts.slice(0, 10).map((alert) => (
                    <div
                      key={alert.id}
                      className="p-4 bg-green-500/5 border border-green-500/20 rounded-lg hover:bg-green-500/10 transition-colors"
                      data-testid={`alert-${alert.team_name}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-green-100">{alert.team_name}</span>
                            <span className="text-green-300/70">vs</span>
                            <span className="text-green-100">{alert.opponent}</span>
                            <Badge variant="outline" className="border-green-500 text-green-400 ml-2">
                              {alert.score}
                            </Badge>
                          </div>
                          <p className="text-sm text-green-300/70 mb-2">{alert.reason}</p>
                          <div className="flex items-center gap-2 text-xs text-green-300/60">
                            <Clock className="h-3 w-3" />
                            <span>{alert.minute}'</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`text-2xl font-bold ${getComebackColor(alert.probability)}`}>
                            {Math.round(alert.probability)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;