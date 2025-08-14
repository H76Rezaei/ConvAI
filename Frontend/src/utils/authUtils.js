export const getCurrentUser = () => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      user_id: payload.user_id,
      email: payload.email,
      username: payload.username
    };
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

export const getCurrentUserId = () => {
  const user = getCurrentUser();
  return user?.user_id?.toString() || null;
};