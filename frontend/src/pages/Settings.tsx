import { useState } from 'react';
import {
  User,
  Building2,
  Bell,
  Shield,
  Palette,
  Key,
  Save,
  Users,
} from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { currentUser, teamMembers } from '@/data/mockData';
import { cn } from '@/lib/utils';

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'team', label: 'Team', icon: Building2 },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'preferences', label: 'Preferences', icon: Palette },
];

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <MainLayout>
      <div className="p-6 lg:p-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="text-muted-foreground mt-1">
              Manage your account settings and preferences
            </p>
          </div>

          <div className="flex flex-col lg:flex-row gap-8">
            {/* Sidebar Navigation */}
            <nav className="lg:w-56 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'flex items-center gap-3 w-full px-4 py-2.5 rounded-lg text-sm transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>

            {/* Content */}
            <div className="flex-1">
              {activeTab === 'profile' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-xl bg-card border border-border p-6">
                    <h2 className="text-lg font-semibold mb-6">
                      Profile Information
                    </h2>

                    {/* Avatar */}
                    <div className="flex items-center gap-4 mb-6">
                      <Avatar className="h-20 w-20 border-2 border-primary/20">
                        <AvatarFallback className="bg-primary/10 text-primary text-xl font-semibold">
                          {currentUser.name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <Button variant="outline" size="sm">
                          Change Photo
                        </Button>
                        <p className="text-xs text-muted-foreground mt-1">
                          JPG, PNG or GIF. Max 2MB.
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name</Label>
                        <Input
                          id="firstName"
                          defaultValue={currentUser.name.split(' ')[0]}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name</Label>
                        <Input
                          id="lastName"
                          defaultValue={currentUser.name.split(' ')[1]}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" defaultValue={currentUser.email} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="role">Role</Label>
                        <Input id="role" defaultValue={currentUser.role} />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="team">Team</Label>
                        <Select defaultValue={currentUser.team}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Powertrain & EV Systems">
                              Powertrain & EV Systems
                            </SelectItem>
                            <SelectItem value="Legal">Legal</SelectItem>
                            <SelectItem value="Finance">Finance</SelectItem>
                            <SelectItem value="IT Hardware">
                              IT Hardware
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="flex justify-end mt-6 pt-4 border-t border-border">
                      <Button>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'team' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-xl bg-card border border-border p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className="text-lg font-semibold">Team Members</h2>
                        <p className="text-sm text-muted-foreground">
                          Manage your team's access and permissions
                        </p>
                      </div>
                      <Button size="sm">
                        <Users className="w-4 h-4 mr-2" />
                        Invite Member
                      </Button>
                    </div>

                    <div className="space-y-3">
                      {teamMembers.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border"
                        >
                          <div className="flex items-center gap-3">
                            <Avatar className="h-10 w-10">
                              <AvatarFallback className="bg-primary/10 text-primary text-sm">
                                {member.name
                                  .split(' ')
                                  .map((n) => n[0])
                                  .join('')}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium text-sm">
                                {member.name}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {member.email}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-xs text-muted-foreground px-2 py-1 rounded-md bg-muted">
                              {member.role}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {member.team}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-xl bg-card border border-border p-6">
                    <h2 className="text-lg font-semibold mb-6">
                      Notification Preferences
                    </h2>

                    <div className="space-y-4">
                      {[
                        {
                          title: 'RFQ Approved',
                          description:
                            'Receive notifications when an RFQ is approved',
                          defaultChecked: true,
                        },
                        {
                          title: 'Review Required',
                          description:
                            'Get notified when an RFQ needs your review',
                          defaultChecked: true,
                        },
                        {
                          title: 'Document Uploaded',
                          description:
                            'Notify when new documents are added to knowledge base',
                          defaultChecked: false,
                        },
                        {
                          title: 'Team Activity',
                          description:
                            "Updates about your team's RFQ activity",
                          defaultChecked: true,
                        },
                        {
                          title: 'Weekly Digest',
                          description:
                            'Receive a weekly summary of all activity',
                          defaultChecked: true,
                        },
                      ].map((notification, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border"
                        >
                          <div>
                            <p className="font-medium text-sm">
                              {notification.title}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {notification.description}
                            </p>
                          </div>
                          <Switch
                            defaultChecked={notification.defaultChecked}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'security' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-xl bg-card border border-border p-6">
                    <h2 className="text-lg font-semibold mb-6">
                      Security Settings
                    </h2>

                    <div className="space-y-6">
                      {/* Password */}
                      <div className="space-y-4">
                        <h3 className="text-sm font-medium flex items-center gap-2">
                          <Key className="w-4 h-4" />
                          Change Password
                        </h3>
                        <div className="grid gap-4 max-w-md">
                          <div className="space-y-2">
                            <Label htmlFor="currentPassword">
                              Current Password
                            </Label>
                            <Input
                              id="currentPassword"
                              type="password"
                              placeholder="••••••••"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="newPassword">New Password</Label>
                            <Input
                              id="newPassword"
                              type="password"
                              placeholder="••••••••"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="confirmPassword">
                              Confirm New Password
                            </Label>
                            <Input
                              id="confirmPassword"
                              type="password"
                              placeholder="••••••••"
                            />
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          Update Password
                        </Button>
                      </div>

                      <Separator />

                      {/* Two-Factor */}
                      <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border">
                        <div>
                          <p className="font-medium text-sm">
                            Two-Factor Authentication
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Add an extra layer of security to your account
                          </p>
                        </div>
                        <Switch />
                      </div>

                      {/* Sessions */}
                      <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border">
                        <div>
                          <p className="font-medium text-sm">Active Sessions</p>
                          <p className="text-xs text-muted-foreground">
                            Manage and log out of your active sessions
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          View Sessions
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'preferences' && (
                <div className="space-y-6 animate-fade-in">
                  <div className="rounded-xl bg-card border border-border p-6">
                    <h2 className="text-lg font-semibold mb-6">
                      Application Preferences
                    </h2>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Default RFQ Category</Label>
                        <Select defaultValue="EV Components">
                          <SelectTrigger className="max-w-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="EV Components">
                              EV Components
                            </SelectItem>
                            <SelectItem value="Climate Control">
                              Climate Control
                            </SelectItem>
                            <SelectItem value="Software">Software</SelectItem>
                            <SelectItem value="IT Hardware">
                              IT Hardware
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Language</Label>
                        <Select defaultValue="en">
                          <SelectTrigger className="max-w-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="en">English</SelectItem>
                            <SelectItem value="fr">French</SelectItem>
                            <SelectItem value="de">German</SelectItem>
                            <SelectItem value="es">Spanish</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <Separator className="my-4" />

                      <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border">
                        <div>
                          <p className="font-medium text-sm">
                            Auto-save Drafts
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Automatically save RFQ drafts while editing
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>

                      <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border">
                        <div>
                          <p className="font-medium text-sm">
                            Show Source Citations
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Display source references in generated RFQs
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>

                      <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border">
                        <div>
                          <p className="font-medium text-sm">
                            Keyboard Shortcuts
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Enable keyboard shortcuts for faster navigation
                          </p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
