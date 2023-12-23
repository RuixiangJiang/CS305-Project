#include<bits/stdc++.h>
const int Nt = 131071, N = 1e5 + 10, M = 2e5 + 10, inf = 0x3f3f3f3f;
int ri() {
    char c = getchar(); int x = 0, f = 1; for(;c < '0' || c > '9'; c = getchar()) if(c == '-') f = -1;
    for(;c >= '0' && c <= '9'; c = getchar()) x = (x << 1) + (x << 3) - '0' + c; return x * f;
}
int D[N], f[N][51], n, K, p; bool vis[N][51];
struct Edge {
    int to[M], nx[M], w[M], pr[N], tp;
    void add(int u, int v, int W) {to[++tp] = v; nx[tp] = pr[u]; pr[u] = tp; w[tp] = W;}
    void Clr() {
        for(int i = 1;i <= n; ++i) pr[i] = 0;
        tp = 0;
    }
}G, R;
struct Node {int u, x;}T[Nt << 1];
Node min(Node a, Node b) {return a.x < b.x ? a : b;}
void Up(int i, int v) {for(T[i += Nt].x = v;i >>= 1;) T[i] = min(T[i << 1], T[i << 1 | 1]);}
void Add(int &a, int b) {a += b; if(a >= p) a -= p;}
void Dij() {
    Up(n, D[n] = 0);
    for(;T[1].x != inf;) {
        int u = T[1].u; Up(u, inf);
        for(int i = R.pr[u], d; i; i = R.nx[i])
            if(D[R.to[i]] > (d = D[u] + R.w[i]))
                Up(R.to[i], D[R.to[i]] = d);
    }
}
int Dfs(int u, int d) {
    if(d < 0 || d > K) return 0;
    if(vis[u][d]) return -1;
    if(~f[u][d]) return f[u][d];
    vis[u][d] = true;
    int ways = 0;
    for(int i = G.pr[u], t; i; i = G.nx[i])
        if(~(t = Dfs(G.to[i], D[u] + d - G.w[i] - D[G.to[i]])))
            Add(ways, t);
        else return -1;
    vis[u][d] = false;
    if(u == n && !d) Add(ways, 1);
    return f[u][d] = ways;
}
int Work() {
    memset(f, -1, sizeof(f));
    memset(vis, 0, sizeof(vis));
    n = ri(); int m = ri(); K = ri(); p = ri();
    for(int i = 1;i <= n; ++i) D[i] = inf; G.Clr(); R.Clr();
    for(int u, v, w;m--;) u = ri(), v = ri(), w = ri(), G.add(u, v, w), R.add(v, u, w);
    Dij(); int ways = 0;
    for(int i = 0;i <= K; ++i) {
        int t = Dfs(1, i);
        if(!~t) return -1;
        Add(ways, t);
    }
    return ways;
}
int main() {
    memset(T, 0x3f, sizeof(T));
    for(int i = 1;i <= 1e5; ++i) T[i + Nt].u = i;
    for(int Ca = ri();Ca--;) printf("%d\n", Work());
    return 0;
}