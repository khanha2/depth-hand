import os
from importlib import import_module
import numpy as np
from .base_regre import base_regre
# from utils.coder import file_pack
from utils.iso_boxes import iso_cube


class base_clean(base_regre):
    """ This class use cleaned data from 3D PCA bounding cube.
    """
    def __init__(self, args):
        super(base_clean, self).__init__(args)
        # self.num_appen = 4
        self.batch_allot = getattr(
            import_module('model.batch_allot'),
            'batch_clean'
        )

    def fetch_batch(self, fetch_size=None):
        if fetch_size is None:
            fetch_size = self.batch_size
        batch_end = self.batch_beg + fetch_size
        # if batch_end >= self.store_size:
        #     self.batch_beg = batch_end
        #     batch_end = self.batch_beg + fetch_size
        #     self.split_end -= self.store_size
        # # print(self.batch_beg, batch_end, self.split_end)
        if batch_end >= self.split_end:
            return None
        self.batch_data['batch_frame'] = np.expand_dims(
            self.store_handle['clean'][self.batch_beg:batch_end, ...],
            axis=-1)
        self.batch_data['batch_poses'] = \
            self.store_handle['pose_c'][self.batch_beg:batch_end, ...]
        self.batch_data['batch_index'] = \
            self.store_handle['index'][self.batch_beg:batch_end, ...]
        self.batch_data['batch_resce'] = \
            self.store_handle['resce'][self.batch_beg:batch_end, ...]
        self.batch_beg = batch_end
        return self.batch_data

    def receive_data(self, thedata, args):
        """ Receive parameters specific to the data """
        super(base_clean, self).receive_data(thedata, args)
        self.store_name = {
            'index': self.train_file,
            'clean': os.path.join(
                self.prepare_dir, 'clean_{}'.format(self.crop_size)),
            'pose_c': os.path.join(self.prepare_dir, 'pose_c'),
            'resce': self.train_file
        }
        self.store_precon = {
            'index': [],
            'poses': [],
            'resce': [],
            'pose_c': ['poses', 'resce'],
            'clean': ['index', 'resce'],
        }

    def draw_random(self, thedata, args):
        import matplotlib.pyplot as mpplot
        from cv2 import resize as cv2resize

        # from colour import Color
        # points3 = np.random.rand(1000, 3)
        # points3[:, 1] *= 2
        # points3[:, 2] *= 4
        # cube = iso_cube()
        # cube.build(points3, 0)
        # corners = cube.get_corners()
        # ax = mpplot.subplot(projection='3d')
        # cube.draw_cube_wire(ax, corners)
        # pose_trans = cube.transform_to_center(points3)
        # ax.scatter(
        #     pose_trans[:, 0], pose_trans[:, 1], pose_trans[:, 2],
        #     color=Color('lightsteelblue').rgb)
        # mpplot.show()
        # sys.exit()

        index_h5 = self.store_handle['index']
        store_size = index_h5.shape[0]
        frame_id = np.random.choice(store_size)
        # frame_id = 0
        img_id = index_h5[frame_id, ...]
        frame_h5 = self.store_handle['clean'][frame_id, ...]
        poses_h5 = self.store_handle['pose_c'][frame_id, ...].reshape(-1, 3)
        resce_h5 = self.store_handle['resce'][frame_id, ...]

        print('[{}] drawing image #{:d} ...'.format(self.name_desc, img_id))
        print(np.min(frame_h5), np.max(frame_h5))
        print(np.histogram(frame_h5, range=(1e-4, np.max(frame_h5))))
        print(np.min(poses_h5, axis=0), np.max(poses_h5, axis=0))
        from colour import Color
        colors = [Color('orange').rgb, Color('red').rgb, Color('lime').rgb]
        mpplot.subplots(nrows=1, ncols=2, figsize=(2 * 5, 1 * 5))

        ax = mpplot.subplot(1, 2, 2)
        mpplot.gca().set_title('test storage read')
        resce3 = resce_h5[0:4]
        cube = iso_cube()
        cube.load(resce3)
        # need to maintain both image and poses at the same scale
        sizel = np.floor(resce3[0]).astype(int)
        ax.imshow(
            cv2resize(frame_h5, (sizel, sizel)),
            cmap=mpplot.cm.bone_r)
        pose3d = cube.trans_scale_to(poses_h5)
        pose2d, _ = cube.project_ortho(pose3d, roll=0, sort=False)
        pose2d *= sizel
        args.data_draw.draw_pose2d(
            ax, thedata,
            pose2d,
        )

        ax = mpplot.subplot(1, 2, 1)
        mpplot.gca().set_title('test output')
        img_name = args.data_io.index2imagename(img_id)
        img = args.data_io.read_image(os.path.join(self.image_dir, img_name))
        ax.imshow(img, cmap=mpplot.cm.bone_r)
        pose_raw = self.yanker(poses_h5, resce_h5, self.caminfo)
        args.data_draw.draw_pose2d(
            ax, thedata,
            args.data_ops.raw_to_2d(pose_raw, thedata)
        )
        rects = cube.proj_rects_3(
            args.data_ops.raw_to_2d, self.caminfo
        )
        for ii, rect in enumerate(rects):
            rect.draw(ax, colors[ii])

        mpplot.savefig(os.path.join(
            args.predict_dir,
            'draw_{}_{}.png'.format(self.name_desc, img_id)))
        if self.args.show_draw:
            mpplot.show()
        print('[{}] drawing image #{:d} - done.'.format(
            self.name_desc, img_id))
