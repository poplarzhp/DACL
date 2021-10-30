import torch
from tqdm import tqdm

def minibatch_k_means(loader,
                      k,
                      max_iters=50,
                      tol=1e-3,
                      device=None,
                      backbone_model=None):
    """
    Do minibatch version of k-means

    Based on https://www.eecs.tufts.edu/~dsculley/papers/fastkmeans.pdf
    """
    tmp_centroids = next(iter(loader))[0][:k]
    tmp_centroids = tmp_centroids.to(device)
    if backbone_model:
        with torch.no_grad():
            tmp_centroids = backbone_model(tmp_centroids)
    # centroids = next(iter(loader))[0][:k].to(device)
    centroids = tmp_centroids.to(device)

    counts = torch.ones(k, device=device)
    prev_norm = torch.tensor(0.0, device=device)

    print('Stating minibatch_k_means')
    for j in range(max_iters):
        if j % 1 == 0:
            print('Mini batch K-Means Epoch: {}'.format(j))
        for X, _ in tqdm(loader):
            # X = X.to(device) there is a change here
            X = X.to(device)
            if backbone_model:
                with torch.no_grad():
                    X = backbone_model(X)
            # b,d b,1,d 1,c,d
            # print(X.shape)
            diffs = X[:, None, :] - centroids[None, :, :]
            labels = diffs.norm(dim=2).min(dim=1)[1]

            counts += torch.bincount(labels, minlength=k).float()
            eta = 1 / counts

            for q in range(k):
                centroids[q] += eta[q] * (diffs[labels == q, q, :]).sum(dim=0)

        norm = torch.norm(centroids, dim=0).sum()

        if torch.abs(norm - prev_norm) < tol:
            print('Converged')
            return counts, centroids
        prev_norm = norm

    print('Finished minibatch_k_means')
    return counts, centroids


def k_means(X, k, max_iters=50, tol=1e-9, device=None):
    """Do standard k-means clustering."""
    n, d = X.shape

    x_min = torch.min(X, dim=0)[0]
    x_max = torch.max(X, dim=0)[0]

    resp = torch.zeros(n, k, dtype=torch.bool, device=device)
    idx = torch.arange(n)

    centroids = torch.rand(k, d, device=device) * (x_max - x_min) + x_min

    prev_distance = torch.tensor(float('inf'), device=device)

    for i in range(max_iters):
        distances = (X[:, None, :] - centroids[None, :, :]).norm(dim=2)
        labels = distances.min(dim=1)[1]
        for j in range(k):
            centroids[j, :] = X[labels == j, :].mean(dim=0)
        resp[:] = False
        resp[idx, labels] = True
        total_distance = distances[resp].sum()

        if torch.abs(total_distance - prev_distance) < tol:
            break
        prev_distance = total_distance

    return resp.float(), centroids