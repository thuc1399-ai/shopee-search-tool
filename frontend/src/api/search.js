const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

export const searchProducts = async ({ keyword, useAI, sortBy, limit = 10 }) => {
    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                keyword,
                use_ai: useAI,
                sort_by: sortBy,
                limit,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const message = errorData?.detail || "Lỗi kết nối đến server";
            throw new Error(message);
        }

        return await response.json();
    } catch (error) {
        console.error("Search API Error:", error);
        throw error;
    }
};
