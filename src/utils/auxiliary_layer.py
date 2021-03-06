import numpy as np
import cv2


def max_mask_size(mask):
    _, col = np.where(mask[:, :, 0]!=0)
    width_max = calc_max(col)
    transposed_mask = mask.transpose(1, 0, 2)
    _, tcol = np.where(transposed_mask[:, :, 0]!=0)
    height_max = calc_max(tcol)
    
    return width_max, height_max


def calc_max(col):
    count = col[0]
    length = 1
    max = 0
    for c in col:
        if c == count:
            length += 1
            count += 1
        else:
            length = 0
            count = c + 1
        
        if length > max:
            max = length

    return max



def calc_sml_size(large_thresh, origin, max):
    ratio = large_thresh / max
    sml = int(np.floor(origin * ratio))
    sml_do2 = sml % 100
    sml_up = sml - sml_do2
    sml_do2 = (sml_do2 // 4) * 4
    sml = sml_up + sml_do2

    return sml

def pre_padding(input, mask, thresh, wi, hi, is_prepad, prepad_px):
    s_w, e_w, s_h, e_h = wi.min(), wi.max(), hi.min(), hi.max()
    size = input.shape

    # print(s_w, e_w, s_h, e_h, thresh, size)
    # if (e_h > size[0] - thresh+1 and s_h < thresh) or (e_w > size[1] - thresh+1 and s_w < thresh):
    #     print('[INFO] Not enable to pre_padding because Mask is too large')
    #     return input, mask, is_prepad
    # else:
    if (size[0] - 1) - e_h < thresh:
        input, mask = _prepad(input, mask, e_h, s_h, 0, thresh, prepad_px)
        is_prepad['hd'] = True

    if (size[1] - 1) - e_w < thresh:
        input, mask = _prepad(input, mask, e_w, s_w, 1, thresh, prepad_px)
        is_prepad['wr'] = True

    if s_h < thresh:
        input, mask = _prepad(input, mask, s_h, e_h, 0, thresh, prepad_px)
        is_prepad['hu'] = True

    if s_w < thresh:
        input, mask = _prepad(input, mask, s_w, e_w, 1, thresh, prepad_px)
        is_prepad['wl'] = True

    return input, mask, is_prepad


def _prepad(input, mask, edg, opp, direction, thresh, prepad_px):
    begin = 0
    end = input.shape[direction] - 1
    if direction == 0:
        if edg > opp:
            if end == edg:
                pad = _create_padding_px(input, 0, opp-1, (1, -1, 3), prepad_px, opp-1)
                input, mask = _concat_pad(input, mask, pad, direction)

            elif end - edg < thresh:
                pad_width = thresh
                pad = _create_padding_px(input, 0, end, (1, -1, 3), prepad_px, opp-1)
                input, mask = _concat_pad(input, mask, pad, direction)
        
        elif edg < opp:
            if begin == edg:
                pad = _create_padding_px(input, 0, opp+1, (1, -1, 3), prepad_px, opp+1)
                input, mask = _concat_pad(input, mask, pad, direction)

            elif edg - begin < thresh:
                pad = _create_padding_px(input, 0, begin, (1, -1, 3), prepad_px, opp+1)
                input, mask = _concat_pad(input, mask, pad, direction)
        else:
            raise RuntimeError('Not prepadding despite this image need prepadding')

    elif direction == 1:
        if edg > opp:
            if end == edg:
                pad = _create_padding_px(input, 1, opp-1, (-1, 1, 3), prepad_px, opp-1)
                input, mask = _concat_pad(input, mask, pad, direction)

            elif end - edg < thresh:
                pad = _create_padding_px(input, 1, end, (-1, 1, 3), prepad_px, opp-1)
                input, mask = _concat_pad(input, mask, pad, direction)
        
        elif edg < opp:
            if begin == edg:
                pad = _create_padding_px(input,  1, opp+1, (-1, 1, 3), prepad_px, opp+1)
                input, mask = _concat_pad(input, mask, pad, direction)

            elif edg - begin < thresh:
                pad = _create_padding_px(input, 1,  begin, (-1, 1, 3), prepad_px, opp+1)
                input, mask = _concat_pad(input, mask, pad, direction)
        else:
            raise RuntimeError('Not prepadding despite this image need prepadding')

    input = input.astype('uint8')
    mask = mask.astype('uint8')
    return input, mask


def _create_padding_px(base, axis, pos, shape, prepad_px, opp):
    if prepad_px == 'edge' or prepad_px == 'default':
        if axis == 0:
            return base[pos, :, :].reshape(shape)
        elif axis == 1:
            return base[:, pos, :].reshape(shape)

    elif prepad_px == 'random':
        if axis == 0:
            return np.random.randint(0, 255, size=base[pos, :, :].shape,
                    dtype=np.uint8).reshape(shape)
        elif axis == 1:
            return np.random.randint(0, 255, size=base[:, pos, :].shape,
                    dtype=np.uint8).reshape(shape)

    elif prepad_px == 'random_pick':
        if axis == 0:
            pos = np.random.randint(0, base.shape[0] - 1)
            return base[pos, :, :].reshape(shape)
        elif axis == 1:
            pos = np.random.randint(0, base.shape[1] - 1)
            return base[:, pos, :].reshape(shape)

    elif prepad_px == 'opposite':
        if axis == 0:
            return base[opp, :, :].reshape(shape)
        elif axis == 1:
            return base[:, opp, :].reshape(shape)



def _concat_pad(input, mask, pad, axis):
    mpad = np.zeros(pad.shape, dtype='uint8')
    for i in range(4):
        input = np.concatenate([input, pad], axis=axis)
        mask = np.concatenate([mask, mpad], axis=axis)

    return input, mask


def cut_padding(out, origin, is_prepad):
    if is_prepad['hu']:
        out = np.delete(out, [0, 1, 2, 3], axis=0)
        is_prepad['hu'] = False

    if is_prepad['wl']:
        out = np.delete(out, [0, 1, 2, 3], axis=1)
        is_prepad['wl'] = False

    if is_prepad['hd']:
        out = np.delete(out, [origin[0], origin[0]+1, origin[0]+2, origin[0]+3], axis=0)
        is_prepad['hd'] = False

    if is_prepad['wr']:
        out = np.delete(out, [origin[1], origin[1]+1, origin[1]+2, origin[1]+3], axis=1)
        is_prepad['wr'] = False

    return out


def pseudo_mask_division(input, out_sml, mask, rec, thresh, div_num, lattice_width):
    print('[INFO] {} division and {} lattice width'.format(str(div_num), lattice_width))
    for r in rec:
        y, x, h, w = r
        if w > thresh and h > thresh:
            if div_num == 4:
                # decide the interval and lattice width
                if lattice_width == 'thin':
                    inter_h, inter_w = int(h * (7/16)), int(w * (7/16))
                    patch_size = int(h / 8)
                elif lattice_width == 'normal':
                    inter_h, inter_w = int(h * (3/8)), int(w * (3/8))
                    patch_size = int(h / 4)
                elif lattice_width == 'thick':
                    inter_h, inter_w = int(h / 4), int(w / 4)
                    patch_size = int(h / 2)

                # the padding for mask division
                if h > thresh:
                    input[y+inter_h:y+inter_h+patch_size, x:x+w, :] = \
                            out_sml[y+inter_h:y+inter_h+patch_size, x:x+w, :]
                    mask[y+inter_h:y+inter_h+patch_size, x:x+w, :] = 0

                if w > thresh:
                    input[y:y+h, x+inter_w:x+inter_w+patch_size, :] = \
                            out_sml[y:y+h, x+inter_w:x+inter_w+patch_size, :]
                    mask[y:y+h, x+inter_w:x+inter_w+patch_size, :] = 0

            elif div_num == 9:
                # decide the interval and lattice width
                if lattice_width == 'thin':
                    inter_h, inter_w = int(h * (7/24)), int(w * (7/24))
                    patch_size = int(h / 16)
                elif lattice_width == 'normal':
                    inter_h, inter_w = int(h / 4), int(w / 4)
                    patch_size = int(h / 8)
                elif lattice_width == 'thick':
                    inter_h, inter_w = int(h / 6), int(w / 6)
                    patch_size = int(h / 4)

                # the padding for mask division
                if h > thresh:
                    input[y+inter_h:y+inter_h+patch_size, x:x+w, :] = \
                            out_sml[y+inter_h:y+inter_h+patch_size, x:x+w, :]
                    mask[y+inter_h:y+inter_h+patch_size, x:x+w, :] = 0
                    input[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :] = \
                            out_sml[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :]
                    mask[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :] = 0

                if w > thresh:
                    input[y:y+h, x+inter_w:x+inter_w+patch_size, :] = \
                            out_sml[y:y+h, x+inter_w:x+inter_w+patch_size, :]
                    mask[y:y+h, x+inter_w:x+inter_w+patch_size, :] = 0
                    input[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :] = \
                            out_sml[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :]
                    mask[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :] = 0
            elif div_num == 16:
                # decide the interval and lattice width
                if lattice_width == 'thin':
                    inter_h, inter_w = int(h * (29/128)), int(w * (29/128))
                    patch_size = int(h / 32)
                elif lattice_width == 'normal':
                    inter_h, inter_w = int(h * (13/64)), int(w * (13/64))
                    patch_size = int(h / 16)
                elif lattice_width == 'thick':
                    inter_h, inter_w = int(h * (5/32)), int(w * (5/32))
                    patch_size = int(h / 8)

                # the padding for mask division
                if h > thresh:
                    input[y+inter_h:y+inter_h+patch_size, x:x+w, :] = \
                            out_sml[y+inter_h:y+inter_h+patch_size, x:x+w, :]
                    mask[y+inter_h:y+inter_h+patch_size, x:x+w, :] = 0
                    input[y + 2*inter_h + patch_size : y + 2*inter_h + 2*patch_size, x:x+w, :] = \
                            out_sml[y + 2*inter_h + patch_size : y + 2*inter_h + 2*patch_size, x:x+w, :]
                    mask[y + 2*inter_h + patch_size : y + 2*inter_h + 2*patch_size, x:x+w, :] = 0
                    input[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :] = \
                            out_sml[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :]
                    mask[y+h-inter_h-patch_size:y+h-inter_h, x:x+w, :] = 0

                if w > thresh:
                    input[y:y+h, x+inter_w:x+inter_w+patch_size, :] = \
                            out_sml[y:y+h, x+inter_w:x+inter_w+patch_size, :]
                    mask[y:y+h, x+inter_w:x+inter_w+patch_size, :] = 0
                    input[y:y+h, x + 2*inter_w + patch_size : x + 2*inter_w + 2*patch_size, :] = \
                            out_sml[y:y+h, x+inter_w:x+inter_w+patch_size, :]
                    mask[y:y+h, x + 2*inter_w + patch_size : x + 2*inter_w + 2*patch_size, :] = 0
                    input[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :] = \
                            out_sml[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :]
                    mask[y:y+h, x+w-inter_w-patch_size:x+w-inter_w, :] = 0

            print('[INFO] Devided small mask size: (h: {}, w: {})'.format(inter_h, inter_w))
    return input, mask


# the following functions have not beed used (2018/11/02)

# def prepad(input, mask, is_prepad, f_name, list, line):
#     for i in range(thresh):
#         pad_raw = input[list[list.index(line)+i+1], :, :].reshape(1, -1, 3)
#         pad_raws.append(pad_raw)
# 
#     prepad = np.concatenate(pad_raws, axis=0)
#     input = np.concatenate([input, prepad], axis=0)
#     mask = np.concatenate([mask, np.zeros(prepad.shape, dtype='uint8')], axis=0)
#     is_prepad[f_name] = True
# 
#     return input, mask, is_prepad
# 
# 
# def detect_large_mask(mask):
#     idx, col = np.where(mask[:, :, 0]!=0)
#     print(idx)
#     print(col)
#     seq_h, seq_w = [], []
#     rec = []
#     # idx_setは縦に並んでいる数が高さになる．厳密にはマスクがある場所のyのindex
#     idx_set = list(sorted(set(idx)))
#     print(idx_set)
#     print(len(idx_set))
#     for i in idx_set:
#         # 全マスクのyのindexに対して，いくつそのyがidxの方に並んでいるかをみて，xのindexが閾値以上並んでいる場合は，そのyのindexとxがいくつ並んでいるかを追加する．
#         # if np.sum(idx == i) >= thresh:
#         seq_h.append([i, np.sum(idx == i)])
# 
#     if seq_h != []:
#         # print('seq_h: {}'.format(np.array(seq_h)))
#         # print('seq_h.shape: {}'.format(np.array(seq_h).shape))
#         seq_h = np.array(seq_h)
#         seq_h_set = np.array(list(set(seq_h[:, 1])))
#         # print('seq_h_set: {}'.format(np.array(seq_h_set)))
#         # print('seq_h_set.shape: {}'.format(np.array(seq_h_set).shape))
# 
#         seq_h_div = []
#         for i in seq_h_set:
#             seq_h_div.append(seq_h[seq_h[:, 1] == i])
#         # print('seq_h_div: {}'.format(np.array(seq_h_div)))
#         # print('seq_h_div.shape: {}'.format(np.array(seq_h_div).shape))
# 
#         seq_h_div = np.array(seq_h_div)
#         for i in seq_h_div:
#             s_h, e_h = i[0, 0], i[-1, 0]
#             tmp_rec = np.arange(s_h, e_h+1)
#             # if len(tmp_rec) >= thresh:
#             if np.all(i[:, 0] == tmp_rec):
#                 tmp_idx, tmp_col = np.where([idx==s_h])
#                 s_v = col[tmp_col.min()]
#                 rec.append(np.array([s_h, s_v, len(tmp_rec), i[0, 1]]))
# 
#     return np.array(rec)
# 
# def check_rec_position(mask, out1, out2, ip, length, valid):
#     if np.sum(mask[out1[0]:out1[2], out1[1]:out1[3], 0] > 0) > ip * length / 8:
#         out1 = out2
#     if np.sum(mask[out2[0]:out2[2], out2[1]:out2[3], 0] > 0) > ip * length / 8:
#         if np.all(out1 == out2):
#             valid = False
#         else:
#             out2 = out1
#     
#     return out1, out2, valid
# 
# def arange_rec_out(rec_out, opp_rec, ip, ip_axis):
#     if rec_out.shape[ip_axis] >= ip / 8 and rec_out.shape[ip_axis] < ip:
#         if ip_axis == 0:
#             rec_out = cv2.resize(rec_out, (rec_out.shape[ip_axis+1], ip))
#         if ip_axis == 1:
#             rec_out = cv2.resize(rec_out, (ip, rec_out.shape[ip_axis-1]))
#     elif rec_out.shape[ip_axis] < ip / 8:
#         rec_out = opp_rec
#         
#     return rec_out
# 
# def grid_interpolation(input, mask, rec, rec_w):
#     if rec != []:
#         for r in rec:
#             print('[INFO] detect large mask which (y, x, h, w) is {}'.format(r))
#             valid_lr, valid_ud = True, True
#             y, x, h, w = r
#             g_h = int(h / 8)
#             g_w = int(w / 8)
#             i_h = int(h / rec_w)
#             i_w = int(w / rec_w)
# 
#             # recのsy, sx, ey, ex
#             out_l = [y, x-i_w, y+h, x]
#             out_r = [y, x+w, y+h, x+w+i_w]
#             out_u = [y-i_h, x, y, x+w]
#             out_d = [y+h, x, y+h+i_h, x+w]
#             
#             out_l, out_r, valid_lr = check_rec_position(mask, out_l, out_r, i_w, h, valid_lr)
#             out_u, out_d, valid_ud = check_rec_position(mask, out_u, out_d, i_h, w, valid_ud)
#             
#             if valid_lr:
#                 rec_out_l = input[out_l[0]:out_l[2], out_l[1]:out_l[3], :]
#                 rec_out_r = input[out_r[0]:out_r[2], out_r[1]:out_r[3], :]
#                 rec_out_l = arange_rec_out(rec_out_l, rec_out_r, i_w, 1)
#                 rec_out_r = arange_rec_out(rec_out_r, rec_out_l, i_w, 1)
# 
#                 input[y : y+h, x+2*g_w : x+2*g_w+i_w, :] = (2 * rec_out_l + 1 * rec_out_r) / 3
#                 input[y : y+h, x+w-3*g_w : x+w-3*g_w+i_w, :] = (1 * rec_out_l + 2 * rec_out_r) / 3
#                 # input[y : y+h, x+2*g_w : x+2*g_w+i_w, :] = rec_out_l
#                 # input[y : y+h, x+w-3*g_w : x+w-3*g_w+i_w, :] = rec_out_r
#                 mask[y : y+h, x+2*g_w : x+2*g_w+i_w, :] = 0
#                 mask[y : y+h, x+w-3*g_w : x+w-3*g_w+i_w, :] = 0
# 
#             if valid_ud:
#                 rec_out_u = input[out_u[0]:out_u[2], out_u[1]:out_u[3], :]
#                 rec_out_d = input[out_d[0]:out_d[2], out_d[1]:out_d[3], :]
#                 rec_out_u = arange_rec_out(rec_out_u, rec_out_d, i_h, 0)
#                 rec_out_d = arange_rec_out(rec_out_d, rec_out_u, i_h, 0)
#                 print(rec_out_d.shape)
# 
#                 input[y+2*g_h : y+2*g_h+i_h, x : x+w, :] = (2 * rec_out_u + 1 * rec_out_d) / 3
#                 input[y+h-3*g_h : y+h-3*g_h+i_h, x : x+w, :] = (1 * rec_out_u + 2 * rec_out_d) / 3
#                 # input[y+2*g_h : y+2*g_h+i_h, x : x+w, :] = rec_out_u
#                 # input[y+h-3*g_h : y+h-3*g_h+i_h, x : x+w, :] = rec_out_d
#                 mask[y+2*g_h : y+2*g_h+i_h, x : x+w, :] = 0
#                 mask[y+h-3*g_h : y+h-3*g_h+i_h, x : x+w, :] = 0
# 
#             # rec_mean = (rec_out_l + rec_out_r + rec_out_u.transpose(1, 0, 2) + rec_out_d.transpose(1, 0, 2)) / 4
#             # print(rec_mean.shape)
#             # rec_mean = cv2.resize(rec_mean, (2*g_h, 2*g_w))
#             # print(rec_mean.shape)
#             # print(input[y+3*g_h : y+5*g_h, x+3*g_w : x+5*g_w, :].shape)
#             # input[y+3*g_h : y+5*g_h, x+3*g_w : x+5*g_w, :] = rec_mean
#             # mask[y+3*g_h : y+5*g_h, x+3*g_w : x+5*g_w, :] = 0
# 
# 
#     return input, mask
# 
# 
# if __name__ == '__main__':
#     input = (np.random.rand(40, 20, 3) * 10).astype('uint8')
# 
#     mask = np.zeros((40, 20, 3)).astype('uint8')
#     m = np.ones((8, 16, 3))*3
#     m2 = np.ones((25, 8, 3))*3
#     mask[3:11, 3:19, :] = m
#     mask[10:35, 8:16, :] = m2
# 
#     print(input.shape)
#     print(mask.shape)
# 
#     thresh = 6
#     rec_w = 8
#     n_input = input.copy()
#     n_mask = mask.copy()
#     out256 = np.zeros(input.shape)
#     rec = detect_large_mask(mask, thresh)
#     n_input, n_mask = sparse_patch(n_input, out256, n_mask, rec, [8, 6])
#     # n_input, n_mask = grid_interpolation(n_input, n_mask, rec, rec_w)
# 
#     for i in range(1):
#         print(input[:, :, i]==n_input[:, :, i])
#         print(n_mask[:, :, i])
# 
