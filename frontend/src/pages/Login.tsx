
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { toast } from "sonner";
import { login, getConfig } from "@/api";

const formSchema = z.object({
    username: z.string().min(1, "Username is required"),
    password: z.string().min(1, "Password is required"),
    role: z.string().min(1, "Role is required"),
});

const Login = () => {
    const navigate = useNavigate();
    const [appName, setAppName] = useState("RFQ Deep Agent");
    const [loading, setLoading] = useState(false);

    // Fetch App Name from Backend
    useEffect(() => {
        getConfig().then((data) => {
            if (data.appName) setAppName(data.appName);
        }).catch(console.error);
    }, []);

    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            username: "",
            password: "",
            role: "",
        },
    });

    const onSubmit = async (values: z.infer<typeof formSchema>) => {
        setLoading(true);
        try {
            const data = await login(values.username, values.password);
            // Validate role if needed or just trust the login
            if (data.user.role !== values.role) {
                // Optional: enforce role match if strict
                // toast.error("Role mismatch");
            }
            toast.success(`Welcome back, ${data.user.name}`);
            localStorage.setItem("token", data.token);
            localStorage.setItem("user", JSON.stringify(data.user));
            if (data.instanceId) {
                localStorage.setItem("server_instance_id", data.instanceId);
            }
            navigate("/");
        } catch (error) {
            toast.error("Invalid credentials");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50/50">
            <div className="w-full max-w-[900px] h-[500px] bg-white rounded-xl shadow-lg border overflow-hidden flex">

                {/* Left Side - Design */}
                <div className="w-1/2 p-12 bg-gray-50 flex flex-col justify-center relative border-r">
                    <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px]"></div>

                    <div className="relative z-10 space-y-6">
                        <div className="w-1 h-8 bg-blue-600 mb-6"></div>
                        <div className="space-y-2">
                            <span className="text-xs font-semibold tracking-wider text-gray-500 uppercase">Next-Gen Procurement</span>
                            <h1 className="text-3xl font-bold text-gray-900 leading-tight">
                                RFQ Agent
                            </h1>
                        </div>
                        <p className="text-sm text-gray-500 leading-relaxed max-w-[300px]">
                            Your intelligent partner for precision procurement. Analyze requirements, draft comprehensive RFQs, and validate specifications in seconds.
                        </p>
                    </div>
                </div>

                {/* Right Side - Form */}
                <div className="w-1/2 p-12 flex flex-col justify-center">
                    <div className="mb-8">
                        <h2 className="text-2xl font-semibold text-gray-900">Sign in</h2>
                        <p className="text-sm text-gray-500 mt-1">Please enter your credentials to continue.</p>
                    </div>

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

                            <FormField
                                control={form.control}
                                name="username"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-xs font-medium text-gray-700">Username</FormLabel>
                                        <FormControl>
                                            <Input placeholder="" {...field} className="bg-gray-50/50" />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="password"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-xs font-medium text-gray-700">Password</FormLabel>
                                        <FormControl>
                                            <Input type="password" placeholder="" {...field} className="bg-gray-50/50" />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="role"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-xs font-medium text-gray-700">Role</FormLabel>
                                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                                            <FormControl>
                                                <SelectTrigger className="bg-gray-50/50">
                                                    <SelectValue placeholder="Select role" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="Admin">Admin</SelectItem>
                                                <SelectItem value="Engineering Manager">Engineering Manager</SelectItem>
                                                <SelectItem value="Validator">Validator</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <Button type="submit" className="w-full bg-[#0f172a] hover:bg-[#1e293b] text-white mt-4" disabled={loading}>
                                {loading ? "Signing in..." : "Sign In"}
                            </Button>
                        </form>
                    </Form>
                </div>

            </div>
        </div>
    );
};

export default Login;
